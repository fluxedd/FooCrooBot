function wakeup() {
  setInterval(ping(), 300000);
}

function ping() {
  var http = require("http");
  http.get("http://fierce-sierra-52458.herokuapp.com");
}
