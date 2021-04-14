$(function () {
  // 处理登录表单提交
  var vmAuth = new Vue({
    el: '#vm',
    data: {
      email: '',
      passwd: ''
    },
    methods: {
      onSubmit: function () {
        var $form = $('#vm');
        var $submitButton = $form.find('button[type=submit]');
        $submitButton.attr('disabled', 'disabled');
        var $error = $('#error');
        $error.hide();
        if ($form[0].checkValidity()) { // $form[0]将jQUery Object转换为Dom Element
          var data = {
            email: this.email.trim(),
            passwd: CryptoJS.SHA1(this.passwd).toString()
          };
          postJSON('/api/authenticate', data, function (result) {
            if (result.error) {
              $submitButton.removeAttr('disabled');
              $error.html(result.message);
              $error.show();
            } else {
              location.assign('/');
            }
          });
        } else {
          $submitButton.removeAttr('disabled');
        }
        $form.addClass('was-validated');
      }
    }
  });
  // 登录页面隐藏页面顶部登录按钮区域，并让标题居中
  var $userArea = $('#userArea')
  $userArea.removeAttr('class');
  $userArea.hide();
  var $titleArea = $('#titleArea');
  $titleArea.removeAttr('class');
  $titleArea.addClass('col-12').addClass('text-center');
});