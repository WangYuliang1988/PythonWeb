$(function () {
  var vm = new Vue({
    el: '#vm',
    data: {
      name: '',
      email: '',
      passwd: '',
      rePasswd: ''
    },
    methods: {
      onSubmit: function () {
        var $form = $('#vm');
        var $submitButton = $form.find('button[type=submit]');
        $submitButton.attr('disabled', 'disabled');
        var $error = $('#error');
        $error.hide();
        if ($form[0].checkValidity()) { // $form[0]将jQUery Object转换为Dom Element
          if (this.passwd !== this.rePasswd) {
            $submitButton.removeAttr('disabled');
            $error.html('两次输入的密码不一致');
            $error.show();
          } else {
            var data = {
              name: this.name.trim(),
              email: this.email.trim(),
              passwd: CryptoJS.SHA1(this.password).toString()
            }
            postJSON('/api/users', data, function (result) {
              if (result.error) {
                $submitButton.removeAttr('disabled');
                $error.html(result.message);
                $error.show();
              } else {
                return location.assign('/');
              }
            });
          }
        } else {
          $submitButton.removeAttr('disabled');
        }
        $form.addClass('was-validated');
      }
    }
  });
  // 注册页面隐藏页面顶部登录按钮区域，并让标题居中
  var $userArea = $('#userArea')
  $userArea.removeAttr('class');
  $userArea.hide();
  var $titleArea = $('#titleArea');
  $titleArea.removeAttr('class');
  $titleArea.addClass('col-12').addClass('text-center');
});