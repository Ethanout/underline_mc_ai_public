
import mineflayer from 'mineflayer';
import readline from 'readline';

// 强制 stdout 立即刷新（解决管道缓冲问题）
process.stdout.setDefaultEncoding('utf8');
const originalLog = console.log;
console.log = (...args) => {
  originalLog(...args);
  process.stdout.write('');  // 触发刷新
};

const bot = mineflayer.createBot({
  host: process.env.MC_HOST || 'localhost',
  port: parseInt(process.env.MC_PORT || '25565'),
  username: process.env.MC_USERNAME || 'CommandBot',
  version: false, // 自动检测版本
});

// 等待命令响应的 Promise
let currentCommandResolver = null;
let commandTimeout = null;

bot.once('spawn', () => {
  console.log(JSON.stringify({
    type: 'ready',
    username: bot.username,
    position: bot.entity.position,
  }));
});

bot.on('error', (err) => {
  console.error(JSON.stringify({
    type: 'error',
    error: err.message,
  }));
});

bot.on('kicked', (reason) => {
  console.error(JSON.stringify({
    type: 'kicked',
    reason: reason,
  }));
  process.exit(1);
});

// 监听所有聊天消息（包括命令反馈）
bot.on('message', (message) => {
  const text = message.toString();
  
  console.log(JSON.stringify({
    type: 'chat',
    message: text,
    time: Date.now(),
  }));
  
  // 如果正在等待命令响应，立即返回
  if (currentCommandResolver) {
    clearTimeout(commandTimeout);
    currentCommandResolver(text);
    currentCommandResolver = null;
  }
});

// 从 stdin 读取命令
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', async (line) => {
  try {
    const data = JSON.parse(line);
    
    if (data.type === 'command') {
      // 执行命令并等待响应
      const command = data.command.startsWith('/') ? data.command : '/' + data.command;
      const waitMs = data.wait_ms || 1000;
      
      // 设置响应监听器
      const responsePromise = new Promise((resolve) => {
        currentCommandResolver = resolve;
        commandTimeout = setTimeout(() => {
          if (currentCommandResolver) {
            currentCommandResolver('[超时：无响应]');
            currentCommandResolver = null;
          }
        }, waitMs);
      });
      
      // 发送命令
      bot.chat(command);
      
      // ��待响应
      const response = await responsePromise;
      
      console.log(JSON.stringify({
        type: 'command_response',
        command: data.command,
        output: response,
        success: true,
      }));
    }
    else if (data.type === 'get_position') {
      console.log(JSON.stringify({
        type: 'position',
        position: bot.entity.position,
        yaw: bot.entity.yaw,
        pitch: bot.entity.pitch,
      }));
    }
    else if (data.type === 'get_health') {
      console.log(JSON.stringify({
        type: 'health',
        health: bot.health,
        food: bot.food,
      }));
    }
    else if (data.type === 'ping') {
      console.log(JSON.stringify({
        type: 'pong',
        time: Date.now(),
      }));
    }
  } catch (err) {
    console.error(JSON.stringify({
      type: 'error',
      error: err.message,
    }));
  }
});

bot.on('end', () => {
  process.exit(0);
});
