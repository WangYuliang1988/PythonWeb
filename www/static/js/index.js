// Web开发中，前端页面通常都是由后端代码生成的，为了取代原始的拼接字符串的方式，出现了通过模板生成前端页面的方式，比如JSP、ASP、PHP等，都是使用模板方式生成前端页面。
// 如果在页面上大量使用JavaScript，模板方式同样会导致JavaScript代码和后端代码紧密绑定，难以维护，而其根本原因在于负责处理显示的HTML Dom模型与负责处理数据交互的JavaScript代码没有分割清楚。
// 为了将视图与数据进行最大限度的分离，出现了MVVM（Model-View-ViewModel）模式，Model使用纯JavaScript对象表示，View用纯HTML表示，ViewModel使用Javascript编写。
// ViewModel负责把Model的数据同步到View显示，也负责把View的修改同步回Model，View和Model的绑定是双向的：如果在View中修改了输入的数值，在Model中可以立刻拿到新的值；如果在Model中修改了数值，也会立刻反映到View上。
// 
// 本工程中使用Vue来实现MVVM框架。

var currentPage = 1;

function initVM(data) {
  // 初始化Vue时，指定3个参数：
  var vm = new Vue({
    el: "#vm", // el，根据选择器查找绑定的View
    data: { // data：JavaScript对象表示的Model
      blogs: data.blogs,
      page: data.page
    },
    methods: { // View可以触发的JavaScript函数
    }
  });
}

function loadBlogs(pageIndex) {
  getJSON('/api/blogs', {page: pageIndex}, function (result) {
    if (!result.error) {
      if (pageIndex === 1) {
        initVM(result);
      } else {
        var $blogList = $('#blogList');
        result.blogs.forEach(blog => {
          var html = '<div class="blog-post">' + 
            '<h2 class="blog-post-title"><a href="/blog/' + blog.id + '">' + blog.name + '</a></h2>' +
            '<p class="blog-post-meta">发表于 '+ blog.create_time.toDateTime() + '</p>' +
            '<p>' + blog.summary +'</p>' +
            '<p><a href="/blog/' + blog.id + '">继续阅读</a></p>' +
            '</div>';
            $blogList.append(html);
        });
        if (! result.page.has_next) {
          $('#btnMore').hide();
        }
      }
    }
  });
}

$(function () {
  loadBlogs(currentPage);
});