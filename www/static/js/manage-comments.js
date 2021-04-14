var currentPage = 1;

function initVM(data) {
  var vm = new Vue({
    el: '#vm',
    data: {
      comments: data.comments,
      page: data.page
    },
    methods: {
      deleteComment: function (comment) {
        var content = comment.content.length > 20 ? comment.content.substring(0, 20) + '...' : comment.content;
        if (confirm('确认要删除评论“' + content + '”？删除后不可恢复！')) {
          postJSON('/api/comments/' + comment.id + '/delete', null, function (result) {
            if (result) {
              location.reload();
            }
          });
        }
      }
    }
  });
}

function loadComments(pageIndex) {
  getJSON('/api/comments', {page: pageIndex}, function (result) {
    if (!result.error) {
      if (pageIndex === 1) {
        initVM(result);
      } else {
        $commentList = $('#commentList');
        result.comments.forEach(comment => {
          var html = '<tr>' + 
          '<td><span>' + comment.user_name + '</span></td>' +
          '<td><span>' + comment.content + '</span></td>' +
          '<td><button class="btn btn-sm btn-outline-secondary" onclick="deleteComment(\'' + comment.id + '\', \'' + comment.content + '\')">删除</button></td>' +
          '</tr>';
          $commentList.append(html);
        });
        if (!result.page.has_next) {
          $('#btnMore').hide();
        }
      }
    }
  });
}

function deleteComment(id, content) {
  content = content.length > 20 ? content.substring(0, 20) + '...' : content;
  if (confirm('确认要删除评论“' + content + '”？删除后不可恢复！')) {
    postJSON('/api/comments/' + id + '/delete', null, function (result) {
      if (result) {
        location.reload();
      }
    });
  }
}

$(function () {
  loadComments(currentPage);
});