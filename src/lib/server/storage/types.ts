export interface StoredObject {
  size: number;
  type: string;
}

/** The storage operations the app needs. Implemented by R2 in production and a fake in tests. */
export interface ObjectStore {
  /** URL the browser can PUT one file to, until it expires. */
  presignUpload(key: string, options: { type: string; expiresIn: number }): string;
  /** URL that downloads the object as an attachment, until it expires. */
  presignDownload(key: string, options: { filename: string; expiresIn: number }): string;
  /** Size and type, or null if there is no such object. */
  stat(key: string): Promise<StoredObject | null>;
  /** The first `length` bytes, for checking the real file type. */
  readStart(key: string, length: number): Promise<Uint8Array>;
  delete(key: string): Promise<void>;
}
