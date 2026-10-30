import type { ObjectStore } from "#lib/server/storage/types.js";

/** In-memory ObjectStore for tests. `put` plays the part of the browser's direct upload. */
export function createMemoryStore() {
  const objects = new Map<string, { bytes: Uint8Array; type: string }>();

  const store: ObjectStore = {
    presignUpload: (key, { type, expiresIn }) =>
      `memory://put/${key}?type=${type}&ttl=${expiresIn}`,
    presignDownload: (key, { filename, expiresIn }) =>
      `memory://get/${key}?filename=${encodeURIComponent(filename)}&ttl=${expiresIn}`,
    async stat(key) {
      const object = objects.get(key);
      return object ? { size: object.bytes.length, type: object.type } : null;
    },
    async readStart(key, length) {
      return objects.get(key)?.bytes.slice(0, length) ?? new Uint8Array();
    },
    async delete(key) {
      objects.delete(key);
    }
  };

  return {
    store,
    objects,
    put: (key: string, content: string | Uint8Array, type: string) =>
      objects.set(key, {
        bytes: typeof content === "string" ? new TextEncoder().encode(content) : content,
        type
      })
  };
}
