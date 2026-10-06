// Site behaviour for Alpine.js (CSP build).
//
// The CSP build cannot evaluate JavaScript written inside HTML attributes,
// so every component's logic lives here and templates only reference names:
//   <nav x-data="mobileMenu"> <button @click="toggle"> <div x-show="open">
document.addEventListener("alpine:init", () => {
  window.Alpine.data("mobileMenu", () => ({
    open: false,
    toggle() {
      this.open = !this.open;
    },
    close() {
      this.open = false;
    },
    get closed() {
      return !this.open;
    },
  }));
});
