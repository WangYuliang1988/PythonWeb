/**
 * 通过GET方式发送网络请求，返回JSON格式的结果数据
 * 
 * @param {*} url 请求地址
 * @param {*} data 请求入参
 * @param {*} callback 结果回调函数
 */
function getJSON(url, data, callback) {
  if (typeof (data) === 'object') {
    var arr = [];
    $.each(data, function (k, v) {
      arr.push(k + '=' + encodeURIComponent(v));
    });
    data = arr.join('&');
  }
  _httpJSON('GET', url, data, callback);
}

/**
 * 通过POST方式发送网络请求，返回JSON格式的结果数据
 * 
 * @param {String} url 请求地址
 * @param {*} data 请求入参
 * @param {*} callback 结果回调函数
 */
function postJSON(url, data, callback) {
  _httpJSON('POST', url, data, callback);
}

/**
 * 发送网络请求，返回JSON格式的结果数据
 * 
 * @param {String} method 请求类型：GET 或 POST
 * @param {String} url 请求地址
 * @param {*} data 请求入参
 * @param {*} callback 结果回调函数
 */
function _httpJSON(method, url, data, callback) {
  var opt = {
    type: method,
    dataType: 'json'
  }
  if (method === 'GET') {
    opt.url = url + '?' + data
  }
  if (method === 'POST') {
    opt.url = url;
    opt.data = JSON.stringify(data || {});
    opt.contentType = 'application/json';
  }
  $.ajax(opt).done(function (r) {
    return callback(r);
  }).fail(function (jqXHR, textStatus) {
    let r = {
      error: 'http_bad_response',
      data: jqXHR.status,
      message: 'HTTP: ' + jqXHR.status
    };
    return callback(r);
  });
}

// 扩展Number数据类型的方法，支持将数字转换为格式化的日期字符串
if (! Number.prototype.toDateTime) {
  Number.prototype.toDateTime = function (format) {
    var replaces = {
      'yyyy': function(date) {
          return date.getFullYear().toString();
      },
      'yy': function(date) {
          return (date.getFullYear() % 100).toString();
      },
      'MM': function(date) {
          var m = date.getMonth() + 1;
          return m < 10 ? '0' + m : m.toString();
      },
      'M': function(date) {
          var m = date.getMonth() + 1;
          return m.toString();
      },
      'dd': function(date) {
          var d = date.getDate();
          return d < 10 ? '0' + d : d.toString();
      },
      'd': function(date) {
          var d = date.getDate();
          return d.toString();
      },
      'hh': function(date) {
          var h = date.getHours();
          return h < 10 ? '0' + h : h.toString();
      },
      'h': function(date) {
          var h = date.getHours();
          return h.toString();
      },
      'mm': function(date) {
          var m = date.getMinutes();
          return m < 10 ? '0' + m : m.toString();
      },
      'm': function(date) {
          var m = date.getMinutes();
          return m.toString();
      },
      'ss': function(date) {
          var s = date.getSeconds();
          return s < 10 ? '0' + s : s.toString();
      },
      's': function(date) {
          var s = date.getSeconds();
          return s.toString();
      },
      'a': function(date) {
          var h = date.getHours();
          return h < 12 ? 'AM' : 'PM';
      }
    };
    if (!format) {
      format = 'yyyy-MM-dd hh:mm:ss';
    }
    var token = /([a-zA-Z]+)/;
    var array = format.split(token);
    var date = new Date(this * 1000);
    for (var i = 0; i < array.length; i++) {
      var element = array[i];
      if (element && element in replaces) {
        array[i] = replaces[element](date);
      }
    }
    return array.join('');
  }
}