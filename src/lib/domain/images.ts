/** Formats staff may upload for public photos. Everything is converted to WebP. */
export const IMAGE_UPLOAD_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;
export const MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024; // 10 MB

/** Output size of each kind of public image. */
export const IMAGE_PRESETS = {
  hospitalCover: { width: 1600, height: 900, fit: "cover" }, // 16:9 banner
  hospitalLogo: { width: 400, height: 400, fit: "inside" }, // never cropped
  doctorPhoto: { width: 600, height: 750, fit: "cover" } // 4:5 portrait
} as const;
export type ImagePreset = keyof typeof IMAGE_PRESETS;
