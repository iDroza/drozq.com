# Reply-detection auto-pause (Google Apps Script)

The drip's rule: the moment a lead replies, their sequence pauses, because a
scheduled email landing mid-conversation reads robotic. This script automates
that rule. It runs INSIDE the josh@drozq.com mailbox (Google Apps Script),
checks the inbox every 5 minutes, and POSTs each new sender to
`/api/email/pause` with the platform secret. The endpoint only pauses
subscribers whose status is `active`, so mail from strangers, vendors, or
already-paused people is a harmless no-op. When a pause actually happens, the
script labels the thread **Drip paused** so the automation is visible in the
inbox.

This file is the public template (the repo deploys to drozq.com, so the real
secret can never live here). The filled, paste-ready copy is generated to
`C:\Users\guerr\Downloads\drozq-auto-pause-setup.md`.

## Setup (one time, ~3 minutes, as josh@drozq.com)

1. Open https://script.google.com **logged in as josh@drozq.com** > New project.
2. Name it `drozq drip auto-pause`. Replace the editor contents with the
   script below (the Downloads copy has the secret filled in).
3. Run `autoPauseReplies` once from the toolbar and approve the permission
   prompts (Gmail read/label + external requests).
4. Left sidebar > Triggers (clock icon) > Add Trigger:
   `autoPauseReplies` | Head | Time-driven | Minutes timer | Every 5 minutes.
5. Done. Verify anytime by emailing josh@drozq.com from an enrolled test
   address and watching `python scripts/emailer.py list --status paused`.

## The script (template; real secret in the Downloads copy)

```javascript
var ENDPOINT = "https://drozq.com/api/email/pause";
var SECRET = "PASTE_EMAIL_SECRET_HERE";

function autoPauseReplies() {
  var props = PropertiesService.getScriptProperties();
  var label = GmailApp.getUserLabelByName("Drip paused") ||
              GmailApp.createLabel("Drip paused");
  var threads = GmailApp.search("in:inbox newer_than:2d");

  threads.forEach(function (thread) {
    thread.getMessages().forEach(function (message) {
      var id = message.getId();
      if (props.getProperty("seen_" + id)) return;
      props.setProperty("seen_" + id, "1");

      var match = message.getFrom().match(/[\w.+-]+@[\w-]+\.[\w.-]+/);
      if (!match) return;
      var from = match[0].toLowerCase();
      if (from.indexOf("@drozq.com") !== -1) return; // own domain, skip

      var response = UrlFetchApp.fetch(ENDPOINT, {
        method: "post",
        contentType: "application/json",
        headers: { Authorization: "Bearer " + SECRET },
        payload: JSON.stringify({ email: from, action: "pause" }),
        muteHttpExceptions: true
      });
      try {
        var result = JSON.parse(response.getContentText());
        if (result.ok && result.changed) {
          thread.addLabel(label);
          console.log("Paused drip for " + from);
        }
      } catch (e) {}
    });
  });
}
```

## Behavior notes

- Pauses fire for ANY inbound email from an active subscriber, not just
  literal replies. That is intentional: if a lead emails Joshua about
  anything, they are in conversation and the drip should stand down.
- Resume when the conversation ends: `python scripts/emailer.py resume <email>`.
- Unsubscribed people are never touched (the endpoint's pause only moves
  active to paused).
- The `seen_` properties dedupe processed messages; Apps Script property
  quotas are far above this volume.
