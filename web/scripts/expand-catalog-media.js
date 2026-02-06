#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");

const SUPPORTED_MEDIA_EXTENSIONS = new Set([
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
]);

function parseArgs(argv) {
    const args = {
        input: "web/catalog.json",
        output: "web/catalog.json",
        mediaRoot: "web",
        requireMediaRoots: false,
        adsRoot: "media_profiles/000",
    };

    for (let i = 0; i < argv.length; i += 1) {
        const token = argv[i];
        if (token === "--input" && argv[i + 1]) {
            args.input = argv[++i];
            continue;
        }
        if (token === "--output" && argv[i + 1]) {
            args.output = argv[++i];
            continue;
        }
        if (token === "--media-root" && argv[i + 1]) {
            args.mediaRoot = argv[++i];
            continue;
        }
        if (token === "--ads-root" && argv[i + 1]) {
            args.adsRoot = argv[++i];
            continue;
        }
        if (token === "--require-media-roots") {
            args.requireMediaRoots = true;
            continue;
        }
        if (token === "--help" || token === "-h") {
            printHelpAndExit(0);
        }
        console.error(`Unknown argument: ${token}`);
        printHelpAndExit(1);
    }

    return args;
}

function printHelpAndExit(code) {
    const usage = `
Usage:
  node web/scripts/expand-catalog-media.js [--input <path>] [--output <path>] [--media-root <path>] [--ads-root <path>] [--require-media-roots]

Defaults:
  --input     web/catalog.json
  --output    web/catalog.json
  --media-root web
  --ads-root  media_profiles/000

Behavior:
  - Reads per-profile "media_roots" as folder references.
  - Rebuilds "media" from scratch with expanded file paths from those roots.
  - Interleaves ad media from --ads-root into each profile once (ad will not be first when profile has its own media).
  - If "media_roots" is missing, derives roots from existing "media" entries.
  - Optional strict mode: --require-media-roots fails if a profile has local media files but missing/empty media_roots.
`;
    process.stdout.write(usage.trimStart() + "\n");
    process.exit(code);
}

function isHttpLike(value) {
    return /^https?:\/\//i.test(value);
}

function toPosixPath(value) {
    return value.split(path.sep).join("/");
}

function normalizePathValue(value) {
    return value.replace(/\\/g, "/").replace(/^\/+/, "");
}

function isFolderReference(value) {
    if (typeof value !== "string") return false;
    const trimmed = value.trim();
    if (isHttpLike(trimmed)) return false;
    if (!trimmed) return false;
    if (trimmed.endsWith("/")) return true;
    const ext = path.extname(trimmed).toLowerCase();
    return ext === "";
}

function normalizeMediaRoot(rootValue) {
    return normalizePathValue(rootValue.trim()).replace(/\/+$/, "");
}

function isSupportedLocalMediaFile(value) {
    if (typeof value !== "string") return false;
    const trimmed = value.trim();
    if (!trimmed || isHttpLike(trimmed)) return false;
    const normalized = normalizePathValue(trimmed);
    const ext = path.extname(normalized).toLowerCase();
    return SUPPORTED_MEDIA_EXTENSIONS.has(ext);
}

function deriveRootFromMediaFilePath(filePath) {
    const normalized = normalizePathValue(filePath.trim());
    const dir = path.posix.dirname(normalized);
    if (!dir || dir === ".") return null;
    return dir;
}

function normalizeStringArray(values) {
    if (!Array.isArray(values)) return [];
    return values
        .filter((value) => typeof value === "string")
        .map((value) => value.trim())
        .filter(Boolean);
}

function arraysEqual(a, b) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i += 1) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

function expandMediaRoot(mediaRoot, mediaRootAbs) {
    const normalized = normalizeMediaRoot(mediaRoot);
    const folderAbs = path.resolve(mediaRootAbs, normalized);
    const relativeToRoot = path.relative(mediaRootAbs, folderAbs);

    if (relativeToRoot.startsWith("..") || path.isAbsolute(relativeToRoot)) {
        throw new Error(`Folder reference escapes media root: ${mediaRoot}`);
    }

    if (!fs.existsSync(folderAbs)) {
        throw new Error(`Folder not found for media root: ${mediaRoot}`);
    }

    const stat = fs.statSync(folderAbs);
    if (!stat.isDirectory()) {
        throw new Error(`Media root is not a directory: ${mediaRoot}`);
    }

    const folderPrefix = normalized.replace(/\/+$/, "");
    const discovered = fs
        .readdirSync(folderAbs, { withFileTypes: true })
        .filter((entry) => entry.isFile())
        .map((entry) => entry.name)
        .filter((name) => SUPPORTED_MEDIA_EXTENSIONS.has(path.extname(name).toLowerCase()))
        .sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" }))
        .map((fileName) => toPosixPath(path.posix.join(folderPrefix, fileName)));

    return discovered;
}

function dedupePreserveOrder(values) {
    const seen = new Set();
    const out = [];
    for (const value of values) {
        const key = String(value);
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(value);
    }
    return out;
}

function hashFnv1a(value) {
    const text = String(value);
    let hash = 0x811c9dc5;
    for (let i = 0; i < text.length; i += 1) {
        hash ^= text.charCodeAt(i);
        hash = Math.imul(hash, 0x01000193);
    }
    return hash >>> 0;
}

function deterministicShuffle(values, seed) {
    return values
        .map((value, index) => ({
            value,
            index,
            rank: hashFnv1a(`${seed}::${value}::${index}`),
        }))
        .sort((a, b) => {
            if (a.rank !== b.rank) return a.rank - b.rank;
            return a.index - b.index;
        })
        .map((entry) => entry.value);
}

function interleaveAdsForProfile({
    profileId,
    media,
    mediaRoots,
    adMedia,
    adMediaSet,
    adsRootNormalized,
}) {
    if (!adMedia.length) return media;

    // Skip ad injection for the ad profile itself.
    if (mediaRoots.includes(adsRootNormalized)) return media;

    // Remove ad paths if they already exist, then inject exactly once.
    const profileOnlyMedia = media.filter((item) => !adMediaSet.has(item));
    const shuffledAds = deterministicShuffle(adMedia, `ads:${profileId}`);

    // Enforce "ad is not first": if profile has no own media, skip ad injection.
    if (!profileOnlyMedia.length) return media;

    const firstProfileMedia = profileOnlyMedia[0];
    const remainingPool = [...profileOnlyMedia.slice(1), ...shuffledAds];
    const mixedRemaining = deterministicShuffle(remainingPool, `mix:${profileId}`);
    return dedupePreserveOrder([firstProfileMedia, ...mixedRemaining]);
}

function isUnderRoot(filePath, rootPath) {
    const normalizedFile = normalizePathValue(filePath);
    const normalizedRoot = normalizeMediaRoot(rootPath);
    return normalizedFile === normalizedRoot || normalizedFile.startsWith(`${normalizedRoot}/`);
}

function main() {
    const args = parseArgs(process.argv.slice(2));
    const cwd = process.cwd();
    const inputPath = path.resolve(cwd, args.input);
    const outputPath = path.resolve(cwd, args.output);
    const mediaRootAbs = path.resolve(cwd, args.mediaRoot);

    if (!fs.existsSync(inputPath)) {
        throw new Error(`Input file not found: ${inputPath}`);
    }

    const raw = fs.readFileSync(inputPath, "utf8");
    const data = JSON.parse(raw);

    if (!data || typeof data !== "object" || !Array.isArray(data.profiles)) {
        throw new Error(`Invalid catalog format: expected { profiles: [] } in ${inputPath}`);
    }

    const adsRootNormalized = normalizeMediaRoot(args.adsRoot);
    const adMedia = dedupePreserveOrder(expandMediaRoot(adsRootNormalized, mediaRootAbs));
    const adMediaSet = new Set(adMedia);

    let rootsExpanded = 0;
    let totalRoots = 0;
    let discoveredFiles = 0;
    let hasChanges = false;

    data.profiles = data.profiles.map((profile, index) => {
        if (!profile || typeof profile !== "object") return profile;

        const rawMedia = normalizeStringArray(profile.media);
        const rawMediaRoots = normalizeStringArray(profile.media_roots);
        const hasDeclaredRoots = rawMediaRoots.length > 0;
        const hasLocalMediaFiles = rawMedia.some(
            (mediaEntry) => isSupportedLocalMediaFile(mediaEntry) && !isUnderRoot(mediaEntry, adsRootNormalized)
        );

        if (args.requireMediaRoots && hasLocalMediaFiles && !hasDeclaredRoots) {
            const profileId = (profile.profile || "").toString().trim() || `index_${index}`;
            throw new Error(`Profile ${profileId} has local media files but missing media_roots`);
        }

        const collectedRoots = [];

        for (const root of rawMediaRoots) {
            if (isHttpLike(root)) {
                throw new Error(`Invalid media_roots entry (URLs are not allowed): ${root}`);
            }
            collectedRoots.push(normalizeMediaRoot(root));
        }
        const declaredRootsSet = new Set(collectedRoots);

        for (const mediaEntry of rawMedia) {
            if (isFolderReference(mediaEntry)) {
                collectedRoots.push(normalizeMediaRoot(mediaEntry));
                continue;
            }
            if (isSupportedLocalMediaFile(mediaEntry)) {
                const derivedRoot = deriveRootFromMediaFilePath(mediaEntry);
                if (!hasDeclaredRoots) {
                    if (isUnderRoot(mediaEntry, adsRootNormalized)) {
                        continue;
                    }
                    if (derivedRoot) collectedRoots.push(derivedRoot);
                }
            }
        }

        const finalMediaRoots = dedupePreserveOrder(collectedRoots);
        totalRoots += finalMediaRoots.length;

        const expandedMedia = [];
        for (const mediaRoot of finalMediaRoots) {
            const files = expandMediaRoot(mediaRoot, mediaRootAbs);
            rootsExpanded += 1;
            discoveredFiles += files.length;
            expandedMedia.push(...files);
        }

        // Always rebuild media from discovered files; do not carry stale entries from prior runs.
        const finalMedia = interleaveAdsForProfile({
            profileId: (profile.profile || "").toString().trim() || `index_${index}`,
            media: dedupePreserveOrder(expandedMedia),
            mediaRoots: finalMediaRoots,
            adMedia,
            adMediaSet,
            adsRootNormalized,
        });

        const rootsChanged = !arraysEqual(finalMediaRoots, rawMediaRoots.map((root) => normalizeMediaRoot(root)));
        const mediaChanged = !arraysEqual(finalMedia, rawMedia);
        const structureChanged = !Array.isArray(profile.media_roots) || !Array.isArray(profile.media);
        if (rootsChanged || mediaChanged || structureChanged) hasChanges = true;

        return {
            ...profile,
            media_roots: finalMediaRoots,
            media: finalMedia,
        };
    });

    if (!hasChanges) {
        if (outputPath !== inputPath) {
            fs.copyFileSync(inputPath, outputPath);
        }
        process.stdout.write(
            `Catalog media expansion complete. profiles=${data.profiles.length}, roots=${totalRoots}, roots_expanded=${rootsExpanded}, discovered_files=${discoveredFiles}, output=${outputPath}, changed=no\n`
        );
        return;
    }

    fs.writeFileSync(outputPath, `${JSON.stringify(data, null, 2)}\n`);

    process.stdout.write(
        `Catalog media expansion complete. profiles=${data.profiles.length}, roots=${totalRoots}, roots_expanded=${rootsExpanded}, discovered_files=${discoveredFiles}, output=${outputPath}, changed=yes\n`
    );
}

try {
    main();
} catch (error) {
    console.error(`ERROR: ${error.message}`);
    process.exit(1);
}
