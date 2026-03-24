import telebot
from telebot import types
import random
import json
import os
from datetime import datetime, timedelta
import threading

TOKEN = 'YOUR_BOT_TOKEN_HERE'  # Замените на ваш токен
bot = telebot.TeleBot(TOKEN)

# Файл для сохранения данных
DATA_FILE = 'tictactoe_data.json'
PVP_GAMES_FILE = 'pvp_games.json'

# Загрузка данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_pvp_games():
    if os.path.exists(PVP_GAMES_FILE):
        with open(PVP_GAMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_pvp_games(data):
    with open(PVP_GAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Инициализация данных пользователя
def init_user(user_id, username):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            'username': username,
            'wins_ai': 0,
            'losses_ai': 0,
            'draws_ai': 0,
            'wins_pvp': 0,
            'losses_pvp': 0,
            'draws_pvp': 0,
            'level': 1,
            'exp': 0,
            'games_played': 0,
            'rating': 1000,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data(data)
    return data[user_id_str]

# Обновление опыта и уровня
def update_exp(user_id, result, game_type='ai'):
    data = load_data()
    user_id_str = str(user_id)
    
    # Начисление опыта
    exp_gain = 0
    rating_change = 0
    
    if result == 'win':
        exp_gain = 50
        rating_change = 25 if game_type == 'pvp' else 15
    elif result == 'draw':
        exp_gain = 20
        rating_change = 0
    elif result == 'loss':
        exp_gain = 10
        rating_change = -15 if game_type == 'pvp' else -5
    
    data[user_id_str]['exp'] += exp_gain
    data[user_id_str]['games_played'] += 1
    data[user_id_str]['rating'] += rating_change
    
    # Проверка повышения уровня
    exp_needed = data[user_id_str]['level'] * 100
    level_up = False
    while data[user_id_str]['exp'] >= exp_needed:
        data[user_id_str]['level'] += 1
        data[user_id_str]['exp'] -= exp_needed
        exp_needed = data[user_id_str]['level'] * 100
        level_up = True
    
    save_data(data)
    return exp_gain, rating_change, level_up

# Класс для игры с ИИ
class GameAI:
    def __init__(self, user_id, difficulty='medium'):
        self.user_id = user_id
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_turn = 'X'
        self.game_over = False
        self.winner = None
        self.difficulty = difficulty
    
    def make_move(self, row, col):
        if self.board[row][col] == ' ' and not self.game_over and self.current_turn == 'X':
            self.board[row][col] = 'X'
            if self.check_win():
                self.game_over = True
                self.winner = 'X'
                return True
            elif self.check_draw():
                self.game_over = True
                return True
            self.current_turn = 'O'
            return True
        return False
    
    def check_win(self):
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != ' ':
                return True
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != ' ':
                return True
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return True
        return False
    
    def check_draw(self):
        for row in self.board:
            if ' ' in row:
                return False
        return True
    
    def ai_move(self):
        if self.game_over or self.current_turn != 'O':
            return
        
        if self.difficulty == 'easy':
            move = self.get_random_move()
        elif self.difficulty == 'medium':
            move = self.get_medium_move()
        else:
            move = self.get_best_move()
        
        if move:
            self.board[move[0]][move[1]] = 'O'
            if self.check_win():
                self.game_over = True
                self.winner = 'O'
            elif self.check_draw():
                self.game_over = True
            self.current_turn = 'X'
    
    def get_random_move(self):
        empty_cells = [(i, j) for i in range(3) for j in range(3) if self.board[i][j] == ' ']
        return random.choice(empty_cells) if empty_cells else None
    
    def get_medium_move(self):
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == ' ':
                    self.board[i][j] = 'O'
                    if self.check_win():
                        self.board[i][j] = ' '
                        return (i, j)
                    self.board[i][j] = ' '
        
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == ' ':
                    self.board[i][j] = 'X'
                    if self.check_win():
                        self.board[i][j] = ' '
                        return (i, j)
                    self.board[i][j] = ' '
        
        return self.get_random_move()
    
    def get_best_move(self):
        best_score = -float('inf')
        best_move = None
        
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == ' ':
                    self.board[i][j] = 'O'
                    score = self.minimax(False, -float('inf'), float('inf'))
                    self.board[i][j] = ' '
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)
        
        return best_move if best_move else self.get_random_move()
    
    def minimax(self, is_maximizing, alpha, beta):
        if self.check_win():
            return 1 if is_maximizing else -1
        if self.check_draw():
            return 0
        
        if is_maximizing:
            best_score = -float('inf')
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == ' ':
                        self.board[i][j] = 'O'
                        score = self.minimax(False, alpha, beta)
                        self.board[i][j] = ' '
                        best_score = max(score, best_score)
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            break
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == ' ':
                        self.board[i][j] = 'X'
                        score = self.minimax(True, alpha, beta)
                        self.board[i][j] = ' '
                        best_score = min(score, best_score)
                        beta = min(beta, best_score)
                        if beta <= alpha:
                            break
            return best_score

# Класс для PvP игры
class GamePVP:
    def __init__(self, game_id, player1_id, player1_name):
        self.game_id = game_id
        self.player1_id = player1_id
        self.player2_id = None
        self.player1_name = player1_name
        self.player2_name = None
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_turn = player1_id  # X - создатель
        self.game_over = False
        self.winner = None
        self.last_move_time = datetime.now()
        self.chat_history = []
    
    def add_player2(self, player2_id, player2_name):
        self.player2_id = player2_id
        self.player2_name = player2_name
    
    def make_move(self, player_id, row, col):
        if self.game_over:
            return False, "Игра уже закончена!"
        
        if player_id != self.current_turn:
            return False, "Сейчас не ваш ход!"
        
        if self.board[row][col] != ' ':
            return False, "Эта клетка уже занята!"
        
        symbol = 'X' if player_id == self.player1_id else 'O'
        self.board[row][col] = symbol
        self.last_move_time = datetime.now()
        
        if self.check_win():
            self.game_over = True
            self.winner = player_id
            return True, "win"
        elif self.check_draw():
            self.game_over = True
            return True, "draw"
        
        self.current_turn = self.player2_id if self.current_turn == self.player1_id else self.player1_id
        return True, "continue"
    
    def check_win(self):
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != ' ':
                return True
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != ' ':
                return True
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return True
        return False
    
    def check_draw(self):
        for row in self.board:
            if ' ' in row:
                return False
        return True
    
    def add_message(self, player_id, message):
        player_name = self.player1_name if player_id == self.player1_id else self.player2_name
        self.chat_history.append({
            'player': player_name,
            'message': message,
            'time': datetime.now().strftime('%H:%M')
        })
    
    def get_chat_display(self):
        if not self.chat_history:
            return "💬 Чат пуст"
        
        chat_text = "💬 **Чат игры:**\n"
        for msg in self.chat_history[-10:]:  # Показываем последние 10 сообщений
            chat_text += f"**{msg['player']}** [{msg['time']}]: {msg['message']}\n"
        return chat_text

# Хранилища
ai_games = {}
pvp_games = {}
waiting_players = {}  # Игроки, ожидающие соперника

# Таймер для PvP игр
def check_pvp_timeouts():
    while True:
        threading.Event().wait(30)
        current_time = datetime.now()
        pvp_data = load_pvp_games()
        
        for game_id, game_data in list(pvp_data.items()):
            game = pvp_games.get(game_id)
            if game and not game.game_over:
                time_diff = (current_time - game.last_move_time).seconds
                if time_diff > 60:  # 60 секунд таймаут
                    # Автоматическая победа игроку, который ходит
                    winner = game.current_turn
                    loser = game.player2_id if winner == game.player1_id else game.player1_id
                    
                    game.game_over = True
                    game.winner = winner
                    
                    # Уведомление игроков
                    try:
                        bot.send_message(winner, f"⏰ Противник не сделал ход вовремя! Вы победили!")
                        bot.send_message(loser, f"⏰ Вы не сделали ход вовремя! Игра проиграна!")
                    except:
                        pass
                    
                    # Обновление статистики
                    for player_id in [winner, loser]:
                        result = 'win' if player_id == winner else 'loss'
                        update_exp(player_id, result, 'pvp')
                        
                        if result == 'win':
                            init_user(player_id, "")['wins_pvp'] += 1
                        else:
                            init_user(player_id, "")['losses_pvp'] += 1
                    
                    del pvp_games[game_id]
                    del pvp_data[game_id]
                    save_pvp_games(pvp_data)

# Запуск проверки таймаутов в отдельном потоке
timeout_thread = threading.Thread(target=check_pvp_timeouts, daemon=True)
timeout_thread.start()

# Создание клавиатуры для игры с ИИ
def create_ai_keyboard(game):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = game.board[i][j]
            if cell == ' ':
                text = '⬜'
            elif cell == 'X':
                text = '❌'
            else:
                text = '⭕'
            callback_data = f"ai_move_{i}_{j}"
            row.append(types.InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.row(*row)
    
    keyboard.row(
        types.InlineKeyboardButton("🔄 Новая игра", callback_data="ai_new_game"),
        types.InlineKeyboardButton("⚙️ Сложность", callback_data="ai_difficulty")
    )
    keyboard.row(types.InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
    return keyboard

# Создание клавиатуры для PvP игры
def create_pvp_keyboard(game, player_id):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = game.board[i][j]
            if cell == ' ':
                text = '⬜'
            elif cell == 'X':
                text = '❌'
            else:
                text = '⭕'
            callback_data = f"pvp_move_{game.game_id}_{i}_{j}"
            row.append(types.InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.row(*row)
    
    keyboard.row(
        types.InlineKeyboardButton("💬 Чат", callback_data=f"pvp_chat_{game.game_id}"),
        types.InlineKeyboardButton("🏳 Сдаться", callback_data=f"pvp_surrender_{game.game_id}")
    )
    return keyboard

# Отображение поля для ИИ
def display_ai_board(game, user_id):
    user_data = init_user(user_id, "")
    
    board_display = "🎮 **Аниме-Крестики-Нолики** 🎮\n"
    board_display += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i in range(3):
        row = []
        for j in range(3):
            cell = game.board[i][j]
            if cell == 'X':
                row.append("❌")
            elif cell == 'O':
                row.append("⭕")
            else:
                row.append("⬜")
        board_display += f"  {row[0]}  │  {row[1]}  │  {row[2]}  \n"
        if i < 2:
            board_display += "─────┼─────┼─────\n"
    
    board_display += "\n━━━━━━━━━━━━━━━━━━━━━\n"
    board_display += f"📊 **Статистика:**\n"
    board_display += f"🎚 Уровень: {user_data['level']} | ✨ Опыт: {user_data['exp']}/{user_data['level']*100}\n"
    board_display += f"⭐ Рейтинг: {user_data['rating']}\n"
    board_display += f"🎯 Победы: {user_data['wins_ai']} | Поражения: {user_data['losses_ai']} | Ничьи: {user_data['draws_ai']}\n"
    board_display += f"⚙ Сложность: {game.difficulty.upper()}\n"
    
    if game.game_over:
        board_display += "\n━━━━━━━━━━━━━━━━━━━━━\n"
        if game.winner == 'X':
            board_display += "🎉 **Поздравляю! Ты победил!** 🎉\n"
            board_display += "✨ Твой уровень аниме-мастера растёт! ✨"
        elif game.winner == 'O':
            board_display += "😭 **Ты проиграл...** 😭\n"
            board_display += "💪 Не сдавайся, самурай! 💪"
        else:
            board_display += "🤝 **Ничья!** 🤝\n"
            board_display += "🎌 Хорошая битва! 🎌"
    
    return board_display

# Отображение поля для PvP
def display_pvp_board(game, player_id):
    board_display = "👥 **PvP Режим** 👥\n"
    board_display += "━━━━━━━━━━━━━━━━━━━━━\n"
    board_display += f"**{game.player1_name}** ❌ vs ⭕ **{game.player2_name if game.player2_name else 'Ожидание...'}**\n"
    board_display += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i in range(3):
        row = []
        for j in range(3):
            cell = game.board[i][j]
            if cell == 'X':
                row.append("❌")
            elif cell == 'O':
                row.append("⭕")
            else:
                row.append("⬜")
        board_display += f"  {row[0]}  │  {row[1]}  │  {row[2]}  \n"
        if i < 2:
            board_display += "─────┼─────┼─────\n"
    
    board_display += "\n━━━━━━━━━━━━━━━━━━━━━\n"
    
    if not game.game_over and game.player2_id:
        current_player = "❌ " + game.player1_name if game.current_turn == game.player1_id else "⭕ " + game.player2_name
        board_display += f"🎴 **Ход:** {current_player}\n"
    
    if game.game_over:
        if game.winner:
            winner_name = game.player1_name if game.winner == game.player1_id else game.player2_name
            board_display += f"🏆 **Победитель:** {winner_name}! 🏆\n"
            board_display += "🎊 Великолепная игра! 🎊"
        else:
            board_display += "🤝 **Ничья!** 🤝\n"
    
    board_display += f"\n\n{game.get_chat_display()}"
    
    return board_display

# Главное меню
@bot.message_handler(commands=['start', 'menu'])
def send_menu(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    init_user(user_id, username)
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🤖 Играть с ИИ", callback_data="play_ai"),
        types.InlineKeyboardButton("👥 Играть с игроком", callback_data="play_pvp")
    )
    keyboard.add(
        types.InlineKeyboardButton("📊 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏆 Топ игроков", callback_data="top_players")
    )
    
    welcome_text = "🌸 **Добро пожаловать в Аниме-Крестики-Нолики!** 🌸\n\n"
    welcome_text += "Выбери режим игры:\n"
    welcome_text += "🎮 **Против ИИ** - тренируйся с компьютером\n"
    welcome_text += "👥 **Против игрока** - сразись с другом\n\n"
    welcome_text += "✨ У тебя есть уровень, опыт и рейтинг! ✨"
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard, parse_mode='Markdown')

# Обработка кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    username = call.from_user.first_name
    
    # Главное меню
    if call.data == "main_menu":
        send_menu(call.message)
        bot.answer_callback_query(call.id)
        return
    
    elif call.data == "play_ai":
        ai_games[user_id] = GameAI(user_id, 'medium')
        bot.edit_message_text(
            display_ai_board(ai_games[user_id], user_id),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_ai_keyboard(ai_games[user_id]),
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    elif call.data == "play_pvp":
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("➕ Создать игру", callback_data="create_pvp"),
            types.InlineKeyboardButton("🔍 Найти игру", callback_data="find_pvp")
        )
        keyboard.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        bot.edit_message_text(
            "👥 **PvP Режим**\n\n"
            "Выбери действие:\n"
            "➕ Создать игру - пригласи друга\n"
            "🔍 Найти игру - присоединись к существующей",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    elif call.data == "create_pvp":
        game_id = str(random.randint(100000, 999999))
        pvp_games[game_id] = GamePVP(game_id, user_id, username)
        
        # Сохраняем в ожидающие
        waiting_players[user_id] = game_id
        
        bot.edit_message_text(
            f"🎮 **Игра создана!**\n\n"
            f"ID игры: `{game_id}`\n\n"
            f"Отправь этот ID другу или поделись командой:\n"
            f"`/join {game_id}`\n\n"
            f"⏳ Ожидаем соперника...",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    elif call.data == "find_pvp":
        if waiting_players:
            # Ищем игру, где ждет соперник и это не сам игрок
            for host_id, game_id in waiting_players.items():
                if host_id != user_id and game_id in pvp_games:
                    game = pvp_games[game_id]
                    if not game.player2_id:
                        game.add_player2(user_id, username)
                        del waiting_players[host_id]
                        
                        # Отправляем обоим игрокам
                        for player_id in [host_id, user_id]:
                            bot.send_message(
                                player_id,
                                display_pvp_board(game, player_id),
                                reply_markup=create_pvp_keyboard(game, player_id),
                                parse_mode='Markdown'
                            )
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                        bot.answer_callback_query(call.id, "Соперник найден! Игра началась!")
                        return
        
        bot.answer_callback_query(call.id, "Нет доступных игр. Создай свою!", show_alert=True)
        return
    
    elif call.data == "profile":
        user_data = init_user(user_id, username)
        profile_text = "🌸 **Твой профиль** 🌸\n\n"
        profile_text += f"🎴 **Имя:** {username}\n"
        profile_text += f"🎚 **Уровень:** {user_data['level']}\n"
        profile_text += f"✨ **Опыт:** {user_data['exp']}/{user_data['level']*100}\n"
        profile_text += f"⭐ **Рейтинг:** {user_data['rating']}\n"
        profile_text += f"🎮 **Игр сыграно:** {user_data['games_played']}\n\n"
        profile_text += "**Против ИИ:**\n"
        profile_text += f"🏆 Победы: {user_data['wins_ai']} | 💔 Поражения: {user_data['losses_ai']} | 🤝 Ничьи: {user_data['draws_ai']}\n\n"
        profile_text += "**PvP:**\n"
        profile_text += f"🏆 Победы: {user_data['wins_pvp']} | 💔 Поражения: {user_data['losses_pvp']} | 🤝 Ничьи: {user_data['draws_pvp']}\n"
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        bot.edit_message_text(
            profile_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    elif call.data == "top_players":
        data = load_data()
        players = []
        for uid, info in data.items():
            players.append((info['username'], info['rating'], info['level'], info['wins_pvp']))
        
        players.sort(key=lambda x: x[1], reverse=True)
        
        top_text = "🏆 **Топ игроков по рейтингу** 🏆\n\n"
        for i, (name, rating, level, pvp_wins) in enumerate(players[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
            top_text += f"{medal} **{i}. {name}**\n"
            top_text += f"   ⭐ Рейтинг: {rating} | 🎚 Ур.{level} | 🏆 PvP: {pvp_wins}\n\n"
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        
        bot.edit_message_text(
            top_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return
    
    # Обработка AI ходов
    elif call.data.startswith("ai_"):
        if call.data == "ai_new_game":
            ai_games[user_id] = GameAI(user_id, ai_games[user_id].difficulty)
            bot.edit_message_text(
                display_ai_board(ai_games[user_id], user_id),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_ai_keyboard(ai_games[user_id]),
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id, "Новая игра!")
            return
        
        elif call.data == "ai_difficulty":
            keyboard = types.InlineKeyboardMarkup(row_width=3)
            keyboard.add(
                types.InlineKeyboardButton("Легкий", callback_data="diff_easy"),
                types.InlineKeyboardButton("Средний", callback_data="diff_medium"),
                types.InlineKeyboardButton("Сложный", callback_data="diff_hard")
            )
            keyboard.add(types.InlineKeyboardButton("◀ Назад", callback_data="play_ai"))
            
            bot.edit_message_text(
                "⚙️ **Выбери сложность:**\n\n"
                "🎀 Легкий - для новичков\n"
                "🌸 Средний - оптимальный\n"
                "🔥 Сложный - для мастеров",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id)
            return
        
        elif call.data.startswith("ai_move_"):
            if user_id not in ai_games:
                bot.answer_callback_query(call.id, "Игра не найдена!")
                return
            
            game = ai_games[user_id]
            if game.game_over:
                bot.answer_callback_query(call.id, "Игра уже закончена! Начни новую.")
                return
            
            _, _, row, col = call.data.split('_')
            row, col = int(row), int(col)
            
            if game.make_move(row, col):
                # Проверяем результат
                result = None
                if game.game_over:
                    if game.winner == 'X':
                        exp_gain, rating_change, level_up = update_exp(user_id, 'win', 'ai')
                        result = f"🎉 Победа! +{exp_gain} опыта, +{rating_change} рейтинга!"
                        if level_up:
                            result += f"\n🎊 УРОВЕНЬ ПОВЫШЕН! 🎊"
                        
                        user_data = init_user(user_id, username)
                        user_data['wins_ai'] += 1
                        save_data(load_data())
                    elif game.winner == 'O':
                        exp_gain, rating_change, level_up = update_exp(user_id, 'loss', 'ai')
                        result = f"💔 Поражение... +{exp_gain} опыта, {rating_change} рейтинга"
                        user_data = init_user(user_id, username)
                        user_data['losses_ai'] += 1
                        save_data(load_data())
                    else:
                        exp_gain, rating_change, level_up = update_exp(user_id, 'draw', 'ai')
                        result = f"🤝 Ничья! +{exp_gain} опыта"
                        user_data = init_user(user_id, username)
                        user_data['draws_ai'] += 1
                        save_data(load_data())
                
                bot.edit_message_text(
                    display_ai_board(game, user_id) + (f"\n\n{result}" if result else ""),
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=create_ai_keyboard(game),
                    parse_mode='Markdown'
                )
                
                # Ход бота
                if not game.game_over:
                    game.ai_move()
                    result = None
                    if game.game_over:
                        if game.winner == 'O':
                            exp_gain, rating_change, level_up = update_exp(user_id, 'loss', 'ai')
                            result = f"💔 Поражение... +{exp_gain} опыта, {rating_change} рейтинга"
                            user_data = init_user(user_id, username)
                            user_data['losses_ai'] += 1
                            save_data(load_data())
                        elif game.winner == 'X':
                            exp_gain, rating_change, level_up = update_exp(user_id, 'win', 'ai')
                            result = f"🎉 Победа! +{exp_gain} опыта, +{rating_change} рейтинга!"
                            if level_up:
                                result += f"\n🎊 УРОВЕНЬ ПОВЫШЕН! 🎊"
                            user_data = init_user(user_id, username)
                            user_data['wins_ai'] += 1
                            save_data(load_data())
                        else:
                            exp_gain, rating_change, level_up = update_exp(user_id, 'draw', 'ai')
                            result = f"🤝 Ничья! +{exp_gain} опыта"
                            user_data = init_user(user_id, username)
                            user_data['draws_ai'] += 1
                            save_data(load_data())
                    
                    bot.edit_message_text(
                        display_ai_board(game, user_id) + (f"\n\n{result}" if result else ""),
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=create_ai_keyboard(game),
                        parse_mode='Markdown'
                    )
                
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "Невозможный ход!")
            return
    
    # Обработка смены сложности
    elif call.data.startswith("diff_"):
        difficulty = call.data.split('_')[1]
        if user_id in ai_games:
            ai_games[user_id].difficulty = difficulty
        bot.answer_callback_query(call.id, f"Сложность изменена на {difficulty.upper()}")
        
        # Возвращаем в игру
        if user_id in ai_games:
            bot.edit_message_text(
                display_ai_board(ai_games[user_id], user_id),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_ai_keyboard(ai_games[user_id]),
                parse_mode='Markdown'
            )
        return

# Команда для присоединения к PvP игре
@bot.message_handler(commands=['join'])
def join_pvp_game(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    
    try:
        game_id = message.text.split()[1]
    except:
        bot.reply_to(message, "❌ Используй: `/join [ID игры]`", parse_mode='Markdown')
        return
    
    if game_id not in pvp_games:
        bot.reply_to(message, "❌ Игра с таким ID не найдена!")
        return
    
    game = pvp_games[game_id]
    
    if game.player2_id:
        bot.reply_to(message, "❌ В этой игре уже есть второй игрок!")
        return
    
    if user_id == game.player1_id:
        bot.reply_to(message, "❌ Вы не можете присоединиться к своей игре!")
        return
    
    # Присоединяемся к игре
    game.add_player2(user_id, username)
    
    # Удаляем из ожидающих, если там был
    if game.player1_id in waiting_players:
        del waiting_players[game.player1_id]
    
    # Отправляем обоим игрокам
    for player_id in [game.player1_id, user_id]:
        bot.send_message(
            player_id,
            display_pvp_board(game, player_id),
            reply_markup=create_pvp_keyboard(game, player_id),
            parse_mode='Markdown'
        )
    
    bot.reply_to(message, "✅ Вы присоединились к игре! Ожидайте начала.")

# Обработка PvP ходов
@bot.callback_query_handler(func=lambda call: call.data.startswith("pvp_"))
def handle_pvp(call):
    user_id = call.from_user.id
    username = call.from_user.first_name
    
    if call.data.startswith("pvp_move_"):
        _, _, game_id, row, col = call.data.split('_')
        row, col = int(row), int(col)
        
        if game_id not in pvp_games:
            bot.answer_callback_query(call.id, "Игра не найдена!")
            return
        
        game = pvp_games[game_id]
        
        if user_id not in [game.player1_id, game.player2_id]:
            bot.answer_callback_query(call.id, "Вы не участвуете в этой игре!")
            return
        
        result, message = game.make_move(user_id, row, col)
        
        if result:
            if message == "win" or message == "draw":
                # Игра закончена
                if message == "win":
                    winner = game.winner
                    loser = game.player2_id if winner == game.player1_id else game.player1_id
                    
                    # Обновление статистики
                    for player_id in [winner, loser]:
                        exp_gain, rating_change, level_up = update_exp(player_id, 'win' if player_id == winner else 'loss', 'pvp')
                        user_data = init_user(player_id, "")
                        if player_id == winner:
                            user_data['wins_pvp'] += 1
                        else:
                            user_data['losses_pvp'] += 1
                        save_data(load_data())
                    
                    # Уведомление о победе
                    for player_id in [game.player1_id, game.player2_id]:
                        bot.edit_message_text(
                            display_pvp_board(game, player_id),
                            player_id,
                            call.message.message_id if player_id == user_id else None,
                            reply_markup=create_pvp_keyboard(game, player_id),
                            parse_mode='Markdown'
                        )
                        if player_id != user_id:
                            try:
                                bot.send_message(player_id, "🎮 Игра обновлена!")
                            except:
                                pass
                
                elif message == "draw":
                    for player_id in [game.player1_id, game.player2_id]:
                        update_exp(player_id, 'draw', 'pvp')
                        user_data = init_user(player_id, "")
                        user_data['draws_pvp'] += 1
                        save_data(load_data())
                
                # Удаляем игру
                del pvp_games[game_id]
                pvp_data = load_pvp_games()
                if game_id in pvp_data:
                    del pvp_data[game_id]
                    save_pvp_games(pvp_data)
            
            else:
                # Игра продолжается
                for player_id in [game.player1_id, game.player2_id]:
                    try:
                        bot.edit_message_text(
                            display_pvp_board(game, player_id),
                            player_id,
                            call.message.message_id if player_id == user_id else None,
                            reply_markup=create_pvp_keyboard(game, player_id),
                            parse_mode='Markdown'
                        )
                    except:
                        pass
            
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(call.id, message)
    
    elif call.data.startswith("pvp_chat_"):
        game_id = call.data.split('_')[2]
        if game_id in pvp_games:
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "💬 Введите сообщение для чата:")
            bot.register_next_step_handler(call.message, lambda msg: send_chat_message(msg, game_id, user_id))
    
    elif call.data.startswith("pvp_surrender_"):
        game_id = call.data.split('_')[2]
        if game_id in pvp_games:
            game = pvp_games[game_id]
            if user_id in [game.player1_id, game.player2_id]:
                winner = game.player2_id if user_id == game.player1_id else game.player1_id
                game.game_over = True
                game.winner = winner
                
                # Обновление статистики
                for player_id in [winner, user_id]:
                    exp_gain, rating_change, level_up = update_exp(player_id, 'win' if player_id == winner else 'loss', 'pvp')
                    user_data = init_user(player_id, "")
                    if player_id == winner:
                        user_data['wins_pvp'] += 1
                    else:
                        user_data['losses_pvp'] += 1
                    save_data(load_data())
                
                # Уведомление
                for player_id in [game.player1_id, game.player2_id]:
                    bot.send_message(
                        player_id,
                        display_pvp_board(game, player_id),
                        reply_markup=create_pvp_keyboard(game, player_id),
                        parse_mode='Markdown'
                    )
                
                del pvp_games[game_id]
                bot.answer_callback_query(call.id, "Вы сдались!")
            else:
                bot.answer_callback_query(call.id, "Ошибка!")

def send_chat_message(message, game_id, user_id):
    if game_id in pvp_games:
        game = pvp_games[game_id]
        if user_id in [game.player1_id, game.player2_id]:
            game.add_message(user_id, message.text)
            
            # Обновляем поле для обоих игроков
            for player_id in [game.player1_id, game.player2_id]:
                try:
                    bot.edit_message_text(
                        display_pvp_board(game, player_id),
                        player_id,
                        message.message_id - 1,
                        reply_markup=create_pvp_keyboard(game, player_id),
                        parse_mode='Markdown'
                    )
                except:
                    pass

# Запуск бота
if __name__ == '__main__':
    print("🌸 Бот запущен в аниме-стиле! 🌸")
    bot.polling(none_stop=True)
