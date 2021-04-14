function initVM(data) {
  document.title = data.blog.name + ' - PythonWeb'

  var vm_blog = new Vue({
    el: "#vm_blog",
    data: {
      blog: data.blog,
      comments: data.comments
    },
    methods: {
      onSubmit: function () {
        var $form = $("#form-comment");
        var $submitButton = $form.find('button[type=submit]');
        $submitButton.attr('disabled', 'disabled');
        if ($form[0].checkValidity()) {
          var content = $form.find("textarea").val().trim();
          postJSON("/api/blogs/" + this.$data.blog.id + "/comments", {content: content}, function (result) {
            if (result.error) {
              $submitButton.removeAttr('disabled');
            } else {
              location.reload();
            }
          });
        } else {
          $submitButton.removeAttr('disabled');
        }
        $form.addClass('was-validated');
      }
    }
  });

  var vm_profile = new Vue({
    el: "#vm_profile",
    data: {
      blog: data.blog
    }
  });
}

$(function () {
  getJSON('/api/blogs/' + BLOG_ID, null, function (result) {
    if (! result.error) {
      initVM(result);
    }
  });
});