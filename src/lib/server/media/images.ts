import sharp from "sharp";
import {
  IMAGE_PRESETS,
  IMAGE_UPLOAD_TYPES,
  MAX_IMAGE_UPLOAD_BYTES,
  type ImagePreset
} from "#lib/domain/images.js";

export class ImageError extends Error {
  constructor(
    readonly code: "unsupported" | "too_large" | "unreadable",
    message: string
  ) {
    super(message);
  }
}

/**
 * Turns an uploaded photo into a resized WebP for the public site. The output carries no
 * metadata: EXIF (camera, GPS location, original orientation) is dropped.
 */
export async function toPublicWebp(file: File, preset: ImagePreset): Promise<Uint8Array> {
  if (!(IMAGE_UPLOAD_TYPES as readonly string[]).includes(file.type)) {
    throw new ImageError("unsupported", "Upload a JPG, PNG or WebP image");
  }
  if (file.size > MAX_IMAGE_UPLOAD_BYTES) {
    throw new ImageError("too_large", "Images must be 10 MB or smaller");
  }

  const { width, height, fit } = IMAGE_PRESETS[preset];
  try {
    const output = await sharp(await file.arrayBuffer(), {
      autoOrient: true, // apply the camera's EXIF rotation before it is discarded
      failOn: "error", // reject truncated or corrupt files
      limitInputPixels: 40_000_000 // ~40 MP: rejects "decompression bomb" images
    })
      .resize(width, height, { fit, position: "attention", withoutEnlargement: true })
      .webp({ quality: 80 })
      .toBuffer();
    return new Uint8Array(output);
  } catch {
    throw new ImageError("unreadable", "This file could not be read as an image");
  }
}
