function initVM(blog) {
  var vm = new Vue({
    el: '#vm',
    data: blog,
    methods: {
      onSubmit: function () {
        var $form = $('#vm');
        var $submitButton = $form.find('button[type=submit]');
        $submitButton.attr('disabled', 'disabled');
        var $error = $("#error");
        $error.hide();
        if ($form[0].checkValidity()) { // $form[0]将jQUery Object转换为Dom Element
          var url = '/api/blogs';
          if (BLOG_ID) {
            url = url + '/' + BLOG_ID;
          }
          postJSON(url, this.$data, function (result) {
            if (result.error) {
              $submitButton.removeAttr('disabled');
              $error.html(result.message);
              $error.show();
            } else {
              return location.assign('/');
            }
          });
        } else {
          $submitButton.removeAttr('disabled');
        }
        $form.addClass('was-validated');
      }
    }
  });
}

$(function () {
  if (BLOG_ID) {
    getJSON('/api/blogs/' + BLOG_ID, null, function (result) {
      initVM(result.blog);
    });
  } else {
    var blog = {
      name: '',
      summary: '',
      content: ''
    };
    initVM(blog);
  }
});