(() => {
  "use strict";

  const PLAY_LABELS = new Set(["Sitisha", "Pause"]);
  const START_LABELS = new Set(["Cheza", "Play"]);
  const PAUSE_LABELS = new Set(["Sitisha", "Pause"]);
  const STOP_LABELS = new Set(["Simamisha", "Stop"]);
  const SIGN_LANGUAGE_LABELS = new Set(["Lugha ya ishara", "Sign language"]);
  const RATE_LABELS = {
    Polepole: 0.75,
    Kawaida: 1,
    Haraka: 1.25,
    "Haraka sana": 1.5,
  };

  let sessionActive = false;
  let updateQueued = false;
  let deferAutomaticPauseUntil = 0;
  let pendingPlayUntil = 0;

  const buttonName = (button) =>
    (button?.getAttribute?.("aria-label") || button?.textContent || "").trim();

  const video = () =>
    Array.from(document.querySelectorAll("video")).find(
      (item) => item.offsetWidth > 0 || item.offsetHeight > 0,
    ) || document.querySelector("video");

  const readAloudDialog = () =>
    Array.from(document.querySelectorAll('[role="dialog"]')).find((dialog) =>
      Array.from(dialog.querySelectorAll("button")).some((button) =>
        STOP_LABELS.has(buttonName(button)),
      ),
    );

  const signLanguageButton = () =>
    Array.from(document.querySelectorAll("button")).find((button) =>
      SIGN_LANGUAGE_LABELS.has(buttonName(button)),
    );

  const showSignLanguageVideo = () => {
    const button = signLanguageButton();
    if (button && button.getAttribute("aria-pressed") !== "true") button.click();
  };

  // The stock reader treats any playing video as competing media and pauses
  // narration. Sign-language video is a synchronized visual track, so keep its
  // media event from reaching that global exclusivity handler.
  document.addEventListener(
    "play",
    (event) => {
      if (event.target?.tagName === "VIDEO") event.stopImmediatePropagation();
    },
    true,
  );

  const selectedRate = (dialog) => {
    const checked = dialog?.querySelector(
      '[role="menuitemradio"][aria-checked="true"], [role="menuitemradio"][data-state="checked"]',
    );
    const label = checked ? buttonName(checked) : "";
    if (RATE_LABELS[label]) return RATE_LABELS[label];

    const rateButton = Array.from(dialog?.querySelectorAll("button") || []).find(
      (button) => buttonName(button).startsWith("Kasi ya kucheza:"),
    );
    const selected = buttonName(rateButton).split(":").pop()?.trim();
    return RATE_LABELS[selected] || 1;
  };

  const synchronize = () => {
    updateQueued = false;
    const signVideo = video();
    if (!signVideo) {
      document.documentElement.dataset.mediaSyncState = "waiting-for-video";
      return;
    }
    signVideo.muted = true;
    signVideo.defaultMuted = true;
    signVideo.volume = 0;
    signVideo.playsInline = true;

    const dialog = readAloudDialog();
    const buttons = Array.from(dialog?.querySelectorAll("button") || []);
    const audioIsPlaying = buttons.some((button) =>
      PLAY_LABELS.has(buttonName(button)),
    );

    signVideo.playbackRate = selectedRate(dialog);

    if (audioIsPlaying || performance.now() < pendingPlayUntil) {
      if (!sessionActive || signVideo.ended) signVideo.currentTime = 0;
      sessionActive = true;
      document.documentElement.dataset.mediaSyncState = "playing";
      const playPromise = signVideo.play();
      if (playPromise?.catch) playPromise.catch(() => {});
      return;
    }

    if (performance.now() < deferAutomaticPauseUntil) return;
    signVideo.pause();
    document.documentElement.dataset.mediaSyncState = "paused";
    if (!dialog) sessionActive = false;
  };

  const scheduleSync = () => {
    if (updateQueued) return;
    updateQueued = true;
    requestAnimationFrame(synchronize);
  };

  document.addEventListener(
    "click",
    (event) => {
      const button = event.target.closest?.("button");
      const name = buttonName(button);

      if (button && START_LABELS.has(name)) {
        pendingPlayUntil = performance.now() + 1500;
        deferAutomaticPauseUntil = pendingPlayUntil;
        window.setTimeout(() => {
          showSignLanguageVideo();
          const signVideo = video();
          if (signVideo) {
            signVideo.muted = true;
            signVideo.defaultMuted = true;
            signVideo.volume = 0;
            signVideo.playsInline = true;
            if (!sessionActive || signVideo.ended) signVideo.currentTime = 0;
            signVideo.playbackRate = selectedRate(readAloudDialog());
            const playPromise = signVideo.play();
            if (playPromise?.catch) playPromise.catch(() => {});
          }
          sessionActive = true;
          scheduleSync();
        }, 0);
      }

      const signVideo = video();
      if (button && PAUSE_LABELS.has(name) && signVideo) {
        pendingPlayUntil = 0;
        deferAutomaticPauseUntil = 0;
        signVideo.pause();
      }

      if (button && STOP_LABELS.has(buttonName(button))) {
        if (signVideo) {
          signVideo.pause();
          signVideo.currentTime = 0;
        }
        pendingPlayUntil = 0;
        deferAutomaticPauseUntil = 0;
        sessionActive = false;
      }
      scheduleSync();
    },
    false,
  );

  document.addEventListener(
    "volumechange",
    (event) => {
      if (event.target?.tagName !== "VIDEO") return;
      if (!event.target.muted) event.target.muted = true;
      if (event.target.volume !== 0) event.target.volume = 0;
    },
    true,
  );

  new MutationObserver(scheduleSync).observe(document.documentElement, {
    attributes: true,
    childList: true,
    subtree: true,
    attributeFilter: ["aria-label", "aria-pressed", "aria-checked", "data-state", "class"],
  });

  window.addEventListener("pageshow", scheduleSync);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) video()?.pause();
    else scheduleSync();
  });
  scheduleSync();
})();
