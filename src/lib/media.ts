import { PUBLIC_MEDIA_URL } from "$app/env/public";

/** Public URL of an image stored in the media bucket, or null if there is none. */
export function mediaUrl(key: string | null | undefined): string | null {
  return key ? new URL(key, PUBLIC_MEDIA_URL).href : null;
}
