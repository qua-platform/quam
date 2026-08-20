document$.subscribe(function () {
  var feedback = document.forms.feedback;
  if (typeof feedback === "undefined") return;

  var comment = feedback.querySelector(".md-feedback__comment");
  if (!comment) return;

  // Material's native GA4 integration uses gtag.js, whose dataLayer processor
  // only consumes the arguments form that gtag() pushes. A literal
  // dataLayer.push(["event", ...]) array is silently dropped, so the event must
  // be dispatched through this shim rather than pushed as a raw array.
  function gtag() {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(arguments);
  }

  var page = document.location.pathname;
  var currentRating = null;

  for (var button of feedback.querySelectorAll("[type=submit]")) {
    button.addEventListener("click", function () {
      currentRating = this.getAttribute("data-md-value");
      comment.hidden = false;
    });
  }

  var input = comment.querySelector("textarea");
  var submit = comment.querySelector(".md-feedback__comment-submit");
  submit.addEventListener("click", function (ev) {
    ev.preventDefault();

    var text = input.value.trim();
    if (!text) return;

    gtag("event", "feedback_comment", {
      page: page,
      rating: currentRating,
      comment: text
    });

    input.disabled = true;
    submit.disabled = true;
    submit.textContent = "Thanks for your feedback!";
  });
});
