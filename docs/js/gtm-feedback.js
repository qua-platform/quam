/* Replaces Material's native analytics.provider integration for the
 * feedback widget: same click handling (preventDefault, disable form,
 * reveal note), but reports to GTM's dataLayer instead of calling gtag()
 * directly, since GA4 delivery now goes exclusively through GTM.
 * Also wires the optional free-text comment field revealed after a
 * rating is submitted. */
document$.subscribe(function () {
  var feedback = document.forms.feedback;
  if (typeof feedback === "undefined") return;

  var page = document.location.pathname;
  var currentRating = null;

  for (var button of feedback.querySelectorAll("[type=submit]")) {
    button.addEventListener("click", function (ev) {
      ev.preventDefault();

      var data = this.getAttribute("data-md-value");
      currentRating = data;
      window.dataLayer = window.dataLayer || [];
      dataLayer.push({ event: "md_feedback", page: page, rating: data });

      feedback.firstElementChild.disabled = true;
      var note = feedback.querySelector(
        ".md-feedback__note [data-md-value='" + data + "']"
      );
      if (note) note.hidden = false;

      var comment = feedback.querySelector(".md-feedback__comment");
      if (comment) comment.hidden = false;
    });

    feedback.hidden = false;
  }

  var comment = feedback.querySelector(".md-feedback__comment");
  if (comment) {
    var input = comment.querySelector("textarea");
    var submit = comment.querySelector(".md-feedback__comment-submit");

    submit.addEventListener("click", function (ev) {
      ev.preventDefault();

      var text = input.value.trim();
      if (!text) return;

      window.dataLayer = window.dataLayer || [];
      dataLayer.push({
        event: "md_feedback_comment",
        page: page,
        rating: currentRating,
        comment: text
      });

      input.disabled = true;
      submit.disabled = true;
      submit.textContent = "Thanks for the detail!";
    });
  }
});
