document$.subscribe(function () {
  var feedback = document.forms.feedback;
  if (typeof feedback === "undefined") return;

  var comment = feedback.querySelector(".md-feedback__comment");
  if (!comment) return;

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

    window.dataLayer = window.dataLayer || [];
    dataLayer.push(["event", "feedback_comment", {
      page: page,
      rating: currentRating,
      comment: text
    }]);

    input.disabled = true;
    submit.disabled = true;
    submit.textContent = "Thanks for your feedback!";
  });
});
