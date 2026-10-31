<script lang="ts">
  import HeartPulseIcon from "@lucide/svelte/icons/heart-pulse";
  import { goto } from "$app/navigation";
  import { page } from "$app/state";
  import { safeAdminRedirect } from "#lib/admin/redirect.js";
  import { authClient } from "#lib/auth-client.js";
  import * as Alert from "#lib/components/ui/alert/index.js";
  import { Button } from "#lib/components/ui/button/index.js";
  import * as Card from "#lib/components/ui/card/index.js";
  import * as Field from "#lib/components/ui/field/index.js";
  import { Input } from "#lib/components/ui/input/index.js";
  import * as InputOTP from "#lib/components/ui/input-otp/index.js";
  import { Spinner } from "#lib/components/ui/spinner/index.js";

  const CODE_LENGTH = 6; // matches otpLength in src/lib/server/auth.ts

  let step = $state<"email" | "code">("email");
  let email = $state("");
  let code = $state("");
  let pending = $state(false);
  let errorMessage = $state<string | null>(null);

  /** Turns a better-auth error into something staff can act on, without revealing which emails exist. */
  function describe(error: { status: number; code?: string }) {
    if (error.status === 429) return "Too many attempts. Wait a few minutes, then try again.";
    switch (error.code) {
      case "INVALID_OTP":
        return "That code is not right. Check the latest email and try again.";
      case "OTP_EXPIRED":
        return "That code has expired. Send a new one.";
      case "TOO_MANY_ATTEMPTS":
        return "Too many wrong codes. Send a new one.";
      case "BANNED_USER":
        return "This account is disabled. Ask an administrator for help.";
      case "INVALID_EMAIL":
        return "Enter a valid email address.";
      default:
        return "Something went wrong. Try again.";
    }
  }

  async function sendCode(event?: SubmitEvent) {
    event?.preventDefault();
    pending = true;
    errorMessage = null;
    try {
      const { error } = await authClient.emailOtp.sendVerificationOtp({
        email: email.trim(),
        type: "sign-in"
      });
      if (error) {
        errorMessage = describe(error);
        return;
      }
      code = "";
      step = "code";
    } finally {
      pending = false;
    }
  }

  async function verify(event?: SubmitEvent) {
    event?.preventDefault();
    if (pending || code.length !== CODE_LENGTH) return;
    pending = true;
    errorMessage = null;
    try {
      const { error } = await authClient.signIn.emailOtp({ email: email.trim(), otp: code });
      if (error) {
        errorMessage = describe(error);
        code = "";
        return;
      }
      // safeAdminRedirect only returns /admin paths on this site
      // eslint-disable-next-line svelte/no-navigation-without-resolve
      await goto(safeAdminRedirect(page.url.searchParams.get("redirectTo")), { refreshAll: true });
    } finally {
      pending = false;
    }
  }

  function changeEmail() {
    step = "email";
    code = "";
    errorMessage = null;
  }
</script>

<svelte:head>
  <title>Staff sign-in · Medtour admin</title>
</svelte:head>

<main class="flex min-h-svh items-center justify-center bg-muted p-6">
  <div class="flex w-full max-w-sm flex-col gap-6">
    <div class="flex items-center justify-center gap-2 font-medium">
      <div
        class="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground"
      >
        <HeartPulseIcon class="size-4" />
      </div>
      Medtour admin
    </div>

    <Card.Root>
      <Card.Header>
        <Card.Title class="text-xl">Staff sign-in</Card.Title>
        <Card.Description>
          {#if step === "email"}
            We'll email you a one-time code. No password needed.
          {:else}
            If <span class="font-medium text-foreground">{email.trim()}</span> belongs to a staff
            account, a {CODE_LENGTH}-digit code is on its way. It expires in 5 minutes.
          {/if}
        </Card.Description>
      </Card.Header>

      <Card.Content>
        {#if errorMessage}
          <Alert.Root variant="destructive" class="mb-6">
            <Alert.Description>{errorMessage}</Alert.Description>
          </Alert.Root>
        {/if}

        {#if step === "email"}
          <form onsubmit={sendCode}>
            <Field.Group>
              <Field.Field>
                <Field.Label for="email">Work email</Field.Label>
                <Input
                  id="email"
                  type="email"
                  autocomplete="email"
                  required
                  bind:value={email}
                  disabled={pending}
                />
              </Field.Field>
              <Button type="submit" disabled={pending}>
                {#if pending}<Spinner data-icon="inline-start" />{/if}
                Send code
              </Button>
            </Field.Group>
          </form>
        {:else}
          <form onsubmit={verify}>
            <Field.Group>
              <Field.Field data-invalid={errorMessage ? true : undefined}>
                <Field.Label for="code">Sign-in code</Field.Label>
                <InputOTP.Root
                  inputId="code"
                  maxlength={CODE_LENGTH}
                  inputmode="numeric"
                  pattern="^[0-9]*$"
                  autocomplete="one-time-code"
                  bind:value={code}
                  onComplete={() => verify()}
                  disabled={pending}
                  aria-invalid={errorMessage ? true : undefined}
                >
                  {#snippet children({ cells })}
                    <InputOTP.Group>
                      {#each cells as cell, index (index)}
                        <InputOTP.Slot {cell} />
                      {/each}
                    </InputOTP.Group>
                  {/snippet}
                </InputOTP.Root>
              </Field.Field>
              <Button type="submit" disabled={pending || code.length !== CODE_LENGTH}>
                {#if pending}<Spinner data-icon="inline-start" />{/if}
                Sign in
              </Button>
              <div class="flex justify-between">
                <Button variant="link" class="px-0" onclick={changeEmail} disabled={pending}>
                  Use a different email
                </Button>
                <Button variant="link" class="px-0" onclick={() => sendCode()} disabled={pending}>
                  Send a new code
                </Button>
              </div>
            </Field.Group>
          </form>
        {/if}
      </Card.Content>
    </Card.Root>
  </div>
</main>
