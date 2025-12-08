# 🐍 Hand Tracking Snake Game (AI-Controlled Snake)

*Control the classic Snake game using your hand movements with OpenCV +
Mediapipe + Pygame.*

![Python](https://img.shields.io/badge/Python-3.10-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-Live--Tracking-red)
![Mediapipe](https://img.shields.io/badge/Mediapipe-Hands-green)
![Pygame](https://img.shields.io/badge/Pygame-Game%20Engine-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

## 🚀 Overview

Hand Tracking Snake Game is an AI-powered version of the classic Snake.\
Instead of keyboard arrows, you use hand gestures (index finger
movement) to control the snake direction.

## 🎮 Features

-   Control Snake using **hand gestures**
-   Real-time **index finger tracking**
-   Smooth movement with debounce\
-   **Neon UI**, glowing effects\
-   **Pause / Resume** gesture\
-   Buttons: **New Game**, **Exit**\
-   Camera preview support\
-   FPS-optimized hand tracking

## 📁 Project Structure

    hand-tracking-snake-game/
    │── hand_tracker.py
    │── game.py
    │── main.py
    │── assets/
    │── requirements.txt
    │── README.md

## 🛠️ Installation

``` bash
git clone https://github.com/yourusername/hand-tracking-snake-game.git
cd hand-tracking-snake-game
pip install -r requirements.txt
python main.py
```

## ✊ Hand Controls

  Gesture           Action
  ----------------- -------------
  Move hand left    Snake LEFT
  Move hand right   Snake RIGHT
  Move hand up      Snake UP
  Move hand down    Snake DOWN
  Open hand         Pause
  Pinch gesture     Resume

## 🌱 Future Improvements

-   Difficulty levels\
-   Leaderboard\
-   Gesture-classification ML model\
-   3D background

## ⭐ Support

If you like this project, please **star the repo**!
