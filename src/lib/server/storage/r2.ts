import { S3Client } from "bun";
import type { ObjectStore } from "./types.js";

export interface R2Config {
  endpoint: string; // https://<account-id>.r2.cloudflarestorage.com
  accessKeyId: string;
  secretAccessKey: string;
  bucket: string;
}

/** Cloudflare R2 through Bun's built-in S3 client. */
export function createR2Store(config: R2Config): ObjectStore {
  const client = new S3Client(config);

  return {
    presignUpload: (key, { type, expiresIn }) =>
      client.presign(key, { method: "PUT", type, expiresIn }),

    presignDownload: (key, { filename, expiresIn }) =>
      client.presign(key, {
        method: "GET",
        expiresIn,
        contentDisposition: `attachment; filename="${filename.replace(/["\\\r\n]/g, "_")}"`
      }),

    async stat(key) {
      if (!(await client.exists(key))) return null;
      const { size, type } = await client.stat(key);
      return { size, type };
    },

    async readStart(key, length) {
      return new Uint8Array(await client.file(key).slice(0, length).arrayBuffer());
    },

    async put(key, bytes, type) {
      await client.write(key, bytes, { type });
    },

    async delete(key) {
      await client.delete(key);
    }
  };
}
