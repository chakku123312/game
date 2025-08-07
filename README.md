<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Keyboard Ninja</title>
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Orbitron:wght@500&family=VT323&family=Silkscreen&display=swap" rel="stylesheet">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Press Start 2P', monospace;
      background: radial-gradient(circle at center, #111 0%, #000 100%);
      color: white;
      overflow: hidden;
      height: 100vh;
    }

    #game-title {
      text-align: center;
      font-size: 2.2em;
      margin-top: 30px;
      margin-bottom: 10px;
      color: #00ff00;
      letter-spacing: 2px;
      text-shadow: 2px 2px 8px #000;
    }

    #game {
      position: relative;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
    }

    .letter {
      position: absolute;
      user-select: none;
      transition: transform 0.3s, opacity 0.3s;
      animation: float 1s infinite alternate ease-in-out;
    }

    @keyframes float {
      from { transform: rotate(-5deg); }
      to { transform: rotate(5deg); }
    }

    .explode {
      animation: explode 0.3s forwards;
    }

    @keyframes explode {
      0% { transform: scale(1); opacity: 1; }
      100% { transform: scale(2); opacity: 0; }
    }

    #score, #lives, #high-score {
      position: absolute;
      top: 10px;
      font-size: 16px;
      background: #000a;
      padding: 8px 14px;
      border-radius: 8px;
      z-index: 999;
    }

    #score { left: 10px; }
    #lives { right: 10px; }
    #high-score {
      left: 50%;
      transform: translateX(-50%);
    }

    #game-over {
      position: absolute;
      top: 40%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 20px;
      background: rgba(0, 0, 0, 0.9);
      padding: 30px;
      border-radius: 12px;
      text-align: center;
      display: none;
      z-index: 999;
    }

    #start-btn {
      position: absolute;
      top: 60%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 18px;
      padding: 10px 20px;
      border: none;
      background-color: #00ff00;
      color: black;
      border-radius: 10px;
      cursor: pointer;
      z-index: 999;
    }

    #start-btn:hover {
      background-color: #00dd00;
    }
  </style>
</head>
<body>
  <h1 id="game-title">Keyboard Ninja</h1>
  <div id="game">
    <div id="score">Score: 0</div>
    <div id="lives">Lives: ❤️❤️❤️</div>
    <div id="high-score">High Score: 0</div>
    <div id="game-over">💀 GAME OVER 💀<br><br>Press Start to Try Again</div>
    <button id="start-btn">🚀 Start Game</button>
  </div>

  <!-- Sounds -->
  <audio id="correct-sound" src="https://actions.google.com/sounds/v1/cartoon/pop.ogg"></audio>
  <audio id="wrong-sound" src="https://actions.google.com/sounds/v1/cartoon/clang_and_wobble.ogg"></audio>

  <script>
    const game = document.getElementById('game');
    const scoreDisplay = document.getElementById('score');
    const livesDisplay = document.getElementById('lives');
    const highScoreDisplay = document.getElementById('high-score');
    const gameOverDisplay = document.getElementById('game-over');
    const startBtn = document.getElementById('start-btn');
    const correctSound = document.getElementById('correct-sound');
    const wrongSound = document.getElementById('wrong-sound');
    const gameTitle = document.getElementById('game-title');

    let score = 0;
    let speed = 1.5;
    let lives = 3;
    let letters = [];
    let spawnInterval, updateInterval;
    let gameRunning = false;

    const fonts = ['"Press Start 2P"', '"VT323"', '"Orbitron"', '"Silkscreen"'];

    // High Score logic
    let highScore = localStorage.getItem('keyboardNinjaHighScore') || 0;
    highScoreDisplay.textContent = `High Score: ${highScore}`;

    function randomLetter() {
      const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
      return chars.charAt(Math.floor(Math.random() * chars.length));
    }

    function getRandomColor() {
      const r = Math.floor(180 + Math.random() * 75);
      const g = Math.floor(100 + Math.random() * 155);
      const b = Math.floor(200 + Math.random() * 55);
      return `rgb(${r}, ${g}, ${b})`;
    }

    function getRandomSize() {
      const sizes = ['24px', '32px', '40px', '50px'];
      return sizes[Math.floor(Math.random() * sizes.length)];
    }

    function getRandomFont() {
      return fonts[Math.floor(Math.random() * fonts.length)];
    }

    function spawnLetter() {
      const letter = document.createElement('div');
      const char = randomLetter();
      letter.classList.add('letter');
      letter.textContent = char;
      letter.style.left = Math.random() * (window.innerWidth - 40) + 'px';
      letter.style.top = '0px';
      letter.style.color = getRandomColor();
      letter.style.fontSize = getRandomSize();
      letter.style.fontFamily = getRandomFont();
      game.appendChild(letter);
      letters.push({ el: letter, char: char, y: 0 });
    }

    function updateLetters() {
      for (let i = letters.length - 1; i >= 0; i--) {
        const l = letters[i];
        l.y += speed;
        l.el.style.top = l.y + 'px';

        if (l.y > window.innerHeight - 60) {
          l.el.remove();
          letters.splice(i, 1);
          loseLife();
        }
      }
    }

    function loseLife() {
      lives--;
      updateLives();
      wrongSound.currentTime = 0;
      wrongSound.play().catch(() => {});
      if (lives <= 0) {
        endGame();
      }
    }

    function updateLives() {
      livesDisplay.textContent = `Lives: ${'❤️'.repeat(lives)}`;
    }

    function endGame() {
      clearInterval(spawnInterval);
      clearInterval(updateInterval);
      gameRunning = false;

      // Update high score if beaten
      if (score > highScore) {
        highScore = score;
        localStorage.setItem('keyboardNinjaHighScore', highScore);
        highScoreDisplay.textContent = `High Score: ${highScore}`;
      }

      gameOverDisplay.style.display = 'block';
      startBtn.style.display = 'block';
      gameTitle.style.display = 'block';
    }

    function handleKeyPress(key) {
      for (let i = 0; i < letters.length; i++) {
        if (letters[i].char === key) {
          const el = letters[i].el;
          el.classList.add('explode');
          correctSound.currentTime = 0;
          correctSound.play().catch(() => {});
          setTimeout(() => el.remove(), 300);
          letters.splice(i, 1);
          score++;
          speed += 0.05;
          scoreDisplay.textContent = `Score: ${score}`;
          return;
        }
      }
      loseLife();
    }

    function startGame() {
      letters.forEach(l => l.el.remove());
      letters = [];
      score = 0;
      speed = 1.5;
      lives = 3;
      gameRunning = true;

      scoreDisplay.textContent = "Score: 0";
      updateLives();
      highScoreDisplay.textContent = `High Score: ${highScore}`;
      gameOverDisplay.style.display = 'none';
      startBtn.style.display = 'none';
      gameTitle.style.display = 'none';

      clearInterval(spawnInterval);
      clearInterval(updateInterval);

      spawnInterval = setInterval(spawnLetter, 1000);
      updateInterval = setInterval(updateLetters, 20);
    }

    document.addEventListener('keydown', (e) => {
      if (!gameRunning) return;
      const key = e.key.toUpperCase();
      if (/^[A-Z]$/.test(key)) {
        handleKeyPress(key);
      }
    });

    startBtn.addEventListener('click', startGame);
  </script>
</body>
</html>


