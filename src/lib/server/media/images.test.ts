import sharp from "sharp";
import { describe, expect, test } from "vitest";
import { MAX_IMAGE_UPLOAD_BYTES } from "#lib/domain/images.js";
import { ImageError, toPublicWebp } from "./images.js";

/** A solid-colour test JPEG, optionally with EXIF orientation and a fake private EXIF field. */
async function jpeg(width: number, height: number, orientation?: number) {
  const bytes = await sharp({ create: { width, height, channels: 3, background: "#3366cc" } })
    .jpeg()
    .withMetadata({ orientation, exif: { IFD0: { Copyright: "private-location-data" } } })
    .toBuffer();
  return new File([new Uint8Array(bytes)], "photo.jpg", { type: "image/jpeg" });
}

describe("toPublicWebp", () => {
  test("outputs WebP at the preset size with all metadata removed", async () => {
    const output = await toPublicWebp(await jpeg(4000, 3000), "doctorPhoto");
    const meta = await sharp(output).metadata();

    expect(meta).toMatchObject({ format: "webp", width: 600, height: 750 });
    expect(meta.exif).toBeUndefined();
  });

  test("applies the camera's EXIF rotation before discarding it", async () => {
    // Stored landscape (800×400) but tagged "rotate 90°": it is really a portrait photo
    const output = await toPublicWebp(await jpeg(800, 400, 6), "hospitalLogo");
    expect(await sharp(output).metadata()).toMatchObject({ width: 200, height: 400 });
  });

  test("never enlarges small images", async () => {
    const output = await toPublicWebp(await jpeg(100, 100), "hospitalCover");
    const { width, height } = await sharp(output).metadata();
    expect(width).toBeLessThanOrEqual(100);
    expect(height).toBeLessThanOrEqual(100);
  });

  test("rejects other formats, oversized files and corrupt data", async () => {
    const gif = new File([new Uint8Array(10)], "a.gif", { type: "image/gif" });
    const huge = new File([new Uint8Array(MAX_IMAGE_UPLOAD_BYTES + 1)], "b.jpg", {
      type: "image/jpeg"
    });
    const corrupt = new File([new TextEncoder().encode("not really a jpeg")], "c.jpg", {
      type: "image/jpeg"
    });

    await expect(toPublicWebp(gif, "doctorPhoto")).rejects.toMatchObject({ code: "unsupported" });
    await expect(toPublicWebp(huge, "doctorPhoto")).rejects.toMatchObject({ code: "too_large" });
    await expect(toPublicWebp(corrupt, "doctorPhoto")).rejects.toBeInstanceOf(ImageError);
  });
});
