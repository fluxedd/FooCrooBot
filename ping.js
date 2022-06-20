function wakeup() {
  require("open")("https://fierce-sierra-52458.herokuapp.com", (err) => {
    if (err) throw err;
    console.log("Woke up!");
    setTimeout(wakeup, 1740000); //29m
  });
}
