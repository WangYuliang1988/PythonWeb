var currentPage = 1;

function initVM(data) {
  $('#vm').show();
  var vm = new Vue({
    el: '#vm',
    data: {
      users: data.users,
      page: data.page
    }
  });
}

function loadUsers(pageIndex) {
  getJSON('/api/users', {page: pageIndex}, function (result) {
    if (!result.error) {
      if (pageIndex === 1) {
        initVM(result);
      } else {
        var $userList = $('#userList');
        result.users.forEach(user => {
          var html = '<tr>' +
            '<td><span>' + user.name + '</span>' + (user.admin ? '<span class="text-admin ml-1">(管理员)</span>' : '') + '</td>' +
            '<td><a href="mailto:' + user.email + '">' + user.email + '</a></td>' +
            '<td><span>' + user.create_time.toDateTime() + '</span></td>' +
            '</tr>';
          $userList.append(html);
        });
        if (!result.page.has_next) {
          $('#btnMore').hide();
        }
      }
    }
  });
}

$(function () {
  loadUsers(currentPage);
});