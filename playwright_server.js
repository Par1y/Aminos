const { chromium } = require("playwright");

(async () => {
  const port = 9223; // 定义远程调试端口
  const host = "0.0.0.0"; // 监听所有网络接口

  try {
    // 启动一个可见的浏览器实例，并在所有网络接口上开启远程调试端口
    const browser = await chromium.launch({
      headless: false,
      args: [
        `--remote-debugging-port=${port}`,
        `--remote-debugging-address=${host}`,
      ],
    });

    browser.newPage("about;blank");
    console.log(`(Listening on ${host}:${port})`);

    // 当浏览器被手动关闭时，自动退出脚本
    browser.on("disconnected", () => {
      console.log("Browser was disconnected. Exiting script.");
      process.exit(0);
    });

    // 保持脚本运行，直到浏览器被关闭
    await new Promise(() => {});
  } catch (err) {
    console.error("Failed to launch browser:", err);
    process.exit(1);
  }
})();
