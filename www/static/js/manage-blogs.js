var currentPage = 1;

function initVM(data) {
  var vm = new Vue({
    el: '#vm',
    data: {
      blogs: data.blogs,
      page: data.page
    },
    methods: {
      editBlog: function (blog) {
        location.assign('/manage/blogs/edit?id=' + blog.id);
      },
      deleteBlog: function (blog) {
        if (confirm('确认要删除“' + blog.name + "”？删除后不可恢复！")) {
          postJSON('/api/blogs/' + blog.id + '/delete', null, function (result) {
            if (result) {
              location.reload();
            }
          });
        }
      }
    }
  });
}

function loadBlogs(pageIndex) {
  getJSON('/api/blogs', {page: pageIndex}, function (result) {
    if (!result.error) {
      if (pageIndex === 1) {
        initVM(result);
      } else {
        var $blogList =  $("#blogList");
        result.blogs.forEach(blog => {
          var html = '<tr>' +
            '<td><a target="_blank" href="/blog/' + blog.id + '">' + blog.name + '</a></td>' +
            '<td><span>' + blog.user_name + '</span></td>' +
            '<td><button class="btn btn-sm btn-outline-primary mr-2" onclick="editBlog(\'' + blog.id + '\')">编辑</button><button class="btn btn-sm btn-outline-secondary" onclick="deleteBlog(\'' + blog.id + '\', \'' + blog.name + '\')">删除</button></td>' +
            '</tr>';
          $blogList.append(html);
        });
        if (!result.page.has_next) {
          $("#btnMore").hide();
        }
      }
    }
  });
}

function editBlog(id) {
  location.assign('/manage/blogs/edit?id=' + id);
}

function deleteBlog(id, name) {
  if (confirm('确认要删除“' + name + "”？删除后不可恢复！")) {
    postJSON('/api/blogs/' + id + '/delete', null, function (result) {
      if (result) {
        location.reload();
      }
    });
  }
}

$(function () {
  loadBlogs(currentPage);
});