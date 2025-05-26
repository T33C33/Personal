import tkinter as tk
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageTk
import os
import sys
import random

class NigerianAdventureGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Nigerian Adventure: NYSC Chronicles")
        self.root.geometry("800x600")
        self.root.configure(bg="#f5f5f5")
        
        # Game state variables
        self.player_name = ""
        self.hausa_knowledge = 0
        self.tech_skills = 70  # Starting with decent tech skills as a Mechatronics graduate
        self.social_points = 50
        self.money = 5000  # Starting money in Naira
        self.current_scene = "intro"
        self.inventory = []
        self.friends = []
        self.day = 1
        self.ppa_progress = 0
        
        # Create frames
        self.setup_frames()
        
        # Start with name input
        self.show_name_input()
    
    def setup_frames(self):
        # Header frame
        self.header_frame = tk.Frame(self.root, bg="#008751")  # Nigerian green
        self.header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.title_label = tk.Label(self.header_frame, text="Nigerian Adventure: NYSC Chronicles", 
                                   font=("Arial", 18, "bold"), bg="#008751", fg="white")
        self.title_label.pack(pady=10)
        
        # Main content frame
        self.content_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Image frame
        self.image_frame = tk.Frame(self.content_frame, bg="#f5f5f5")
        self.image_frame.pack(fill=tk.X, pady=10)
        
        # Default image (placeholder)
        self.image_label = tk.Label(self.image_frame, bg="#f5f5f5")
        self.image_label.pack()
        
        # Text frame
        self.text_frame = tk.Frame(self.content_frame, bg="#f5f5f5")
        self.text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.story_text = tk.Text(self.text_frame, wrap=tk.WORD, width=70, height=10, 
                                 font=("Arial", 12), bg="#ffffff", fg="#333333")
        self.story_text.pack(fill=tk.BOTH, expand=True)
        self.story_text.config(state=tk.DISABLED)
        
        # Options frame
        self.options_frame = tk.Frame(self.content_frame, bg="#f5f5f5")
        self.options_frame.pack(fill=tk.X, pady=10)
        
        # Status frame
        self.status_frame = tk.Frame(self.root, bg="#f0f0f0", relief=tk.RAISED, bd=1)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        # Status labels
        self.day_label = tk.Label(self.status_frame, text="Day: 1", bg="#f0f0f0")
        self.day_label.pack(side=tk.LEFT, padx=10)
        
        self.money_label = tk.Label(self.status_frame, text="Money: ₦5,000", bg="#f0f0f0")
        self.money_label.pack(side=tk.LEFT, padx=10)
        
        self.hausa_label = tk.Label(self.status_frame, text="Hausa: 0%", bg="#f0f0f0")
        self.hausa_label.pack(side=tk.LEFT, padx=10)
        
        self.social_label = tk.Label(self.status_frame, text="Social: 50%", bg="#f0f0f0")
        self.social_label.pack(side=tk.LEFT, padx=10)
        
        self.tech_label = tk.Label(self.status_frame, text="Tech: 70%", bg="#f0f0f0")
        self.tech_label.pack(side=tk.LEFT, padx=10)
    
    def show_name_input(self):
        # Clear frames
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        self.update_story_text("Welcome to Nigerian Adventure: NYSC Chronicles!\n\nYou are a Mechatronics Engineering graduate from the University of Port Harcourt, originally from Abia State. You've been posted to Bauchi State for your National Youth Service Corps (NYSC) year, with your Place of Primary Assignment (PPA) at Nascomsoft Embedded, an embedded systems startup.\n\nWhat's your name?")
        
        # Create name entry
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(self.options_frame, textvariable=self.name_var, font=("Arial", 12), width=20)
        name_entry.pack(side=tk.LEFT, padx=10, pady=10)
        
        submit_button = tk.Button(self.options_frame, text="Start Adventure", 
                                 command=self.start_game, bg="#008751", fg="white",
                                 font=("Arial", 12, "bold"))
        submit_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Set default image
        self.set_image("nysc_logo")
    
    def start_game(self):
        self.player_name = self.name_var.get().strip()
        if not self.player_name:
            self.player_name = "Chukwudi"  # Default name if none provided
        
        self.current_scene = "orientation_camp"
        self.render_scene()
    
    def update_story_text(self, text):
        self.story_text.config(state=tk.NORMAL)
        self.story_text.delete(1.0, tk.END)
        self.story_text.insert(tk.END, text)
        self.story_text.config(state=tk.DISABLED)
    
    def update_status(self):
        self.day_label.config(text=f"Day: {self.day}")
        self.money_label.config(text=f"Money: ₦{self.money:,}")
        self.hausa_label.config(text=f"Hausa: {self.hausa_knowledge}%")
        self.social_label.config(text=f"Social: {self.social_points}%")
        self.tech_label.config(text=f"Tech: {self.tech_skills}%")
    
    def set_image(self, image_name):
        # In a real implementation, you would load actual images
        # For this example, we'll create colored rectangles as placeholders
        colors = {
            "nysc_logo": "#008751",  # Nigerian green
            "bauchi": "#D4AF37",     # Gold for Bauchi landscapes
            "market": "#FF5733",     # Orange-red for market
            "office": "#3498DB",     # Blue for office
            "apartment": "#7D3C98",  # Purple for apartment
            "food": "#F1C40F"        # Yellow for food
        }
        
        color = colors.get(image_name, "#CCCCCC")
        
        # Create a colored rectangle as a placeholder
        img = Image.new('RGB', (400, 200), color=color)
        photo = ImageTk.PhotoImage(img)
        
        self.image_label.config(image=photo)
        self.image_label.image = photo  # Keep a reference
    
    def create_option_buttons(self, options):
        # Clear previous options
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Create new option buttons
        for i, (text, scene) in enumerate(options):
            btn = tk.Button(self.options_frame, text=text, 
                           command=lambda s=scene: self.handle_choice(s),
                           bg="#f0c808", fg="#333333",  # Nigerian yellow
                           font=("Arial", 11), width=30, anchor="w")
            btn.pack(fill=tk.X, pady=5)
    
    def handle_choice(self, scene):
        self.current_scene = scene
        
        # Special case handlers
        if scene == "learn_hausa":
            self.hausa_knowledge += 10
            if self.hausa_knowledge > 100:
                self.hausa_knowledge = 100
            self.money -= 500
        elif scene == "buy_food":
            self.money -= 1000
            self.social_points += 5
            self.inventory.append("Local food")
        elif scene == "work_overtime":
            self.tech_skills += 5
            self.money += 2000
            self.social_points -= 5
        elif scene == "make_friend":
            friend = random.choice(["Ibrahim", "Aisha", "Mohammed", "Fatima", "Yusuf"])
            if friend not in self.friends:
                self.friends.append(friend)
            self.social_points += 15
        
        # Advance day for certain scenes
        if scene in ["next_day", "weekend", "work_day_end"]:
            self.day += 1
            # Random events on new days
            if random.random() < 0.3:  # 30% chance of random event
                self.current_scene = random.choice(["random_power_outage", "random_invitation", "random_food"])
        
        # Update status and render the new scene
        self.update_status()
        self.render_scene()
    
    def render_scene(self):
        # Dictionary of scenes with their text, image, and options
        scenes = {
            "orientation_camp": {
                "text": f"Welcome to Bauchi State, {self.player_name}! You've just arrived at the NYSC Orientation Camp. The weather is much drier than Port Harcourt, and you can already feel the cultural differences.\n\nAfter three weeks of parade drills, 'mami market' adventures, and making new friends, you're posted to your PPA: Nascomsoft Embedded in Bauchi city.",
                "image": "nysc_logo",
                "options": [
                    ("Head to your new apartment in Bauchi city", "first_apartment"),
                ]
            },
            "first_apartment": {
                "text": "You arrive at your new apartment, a modest self-contain in a bustling neighborhood. Your landlord, Mallam Adamu, greets you with 'Sannu da zuwa' (Welcome).\n\nYou stare blankly, not understanding a word of Hausa. He switches to English with a heavy accent: 'Ah, corper! You no sabi Hausa? No wahala, you go learn small-small.'",
                "image": "apartment",
                "options": [
                    ("Settle in and rest for the night", "first_morning"),
                    ("Ask Mallam Adamu for basic Hausa phrases", "learn_hausa_intro"),
                ]
            },
            "learn_hausa_intro": {
                "text": "Mallam Adamu laughs heartily. 'Corper, you serious to learn? Okay, make I teach you small-small.'\n\nHe teaches you basic greetings:\n- Sannu (Hello)\n- Yaya gajiya? (How are you?)\n- Na gode (Thank you)\n\nYou practice awkwardly, and he nods approvingly.",
                "image": "apartment",
                "options": [
                    ("Thank him and rest for the night", "first_morning"),
                ]
            },
            "first_morning": {
                "text": f"You wake up to the sound of the muezzin's call to prayer from a nearby mosque. It's 5:30 AM, much earlier than you're used to waking up in Port Harcourt.\n\nToday is your first day at Nascomsoft Embedded. You're excited but nervous about making a good impression.",
                "image": "apartment",
                "options": [
                    ("Get ready and head to the office", "first_day_office"),
                    ("Try to find breakfast first", "find_breakfast"),
                ]
            },
            "find_breakfast": {
                "text": "You step out looking for breakfast. The aroma of frying kosai (bean cakes) and akara fills the air. You spot a woman selling breakfast by the roadside.\n\n'Good morning, ma. I want to buy breakfast,' you say in English.\n\nShe responds in rapid Hausa. You catch only 'kosai' and 'kunu' (millet porridge).",
                "image": "food",
                "options": [
                    ("Point and use hand gestures to order", "breakfast_success"),
                    ("Try your newly learned Hausa phrases", "breakfast_hausa"),
                ]
            },
            "breakfast_hausa": {
                "text": "'Sannu,' you say hesitantly. The woman's face lights up with a smile.\n\n'Sannu! Yaya gajiya?' she responds enthusiastically.\n\nYour Hausa vocabulary is quickly exhausted, but your effort has earned you a generous serving of kosai and kunu at a 'corper-friendly' price.",
                "image": "food",
                "options": [
                    ("Enjoy your breakfast and head to the office", "first_day_office"),
                ]
            },
            "breakfast_success": {
                "text": "Through an elaborate game of charades, you manage to order kosai and kunu. The woman laughs good-naturedly at your efforts.\n\n'Corper new-new,' she says, one of the few English phrases she knows. She gives you extra kosai, saying something that probably means 'welcome to Bauchi.'",
                "image": "food",
                "options": [
                    ("Enjoy your breakfast and head to the office", "first_day_office"),
                ]
            },
            "first_day_office": {
                "text": "You arrive at Nascomsoft Embedded, a small but modern office in a commercial building. The receptionist greets you: 'Ah, you must be the new corper! Oga is expecting you.'\n\nYou're led to meet Mr. Danladi, the CEO, a stern-looking man with glasses who immediately starts questioning you about your Mechatronics knowledge.",
                "image": "office",
                "options": [
                    ("Confidently discuss your final year project on automated systems", "impress_boss"),
                    ("Honestly admit you're nervous but eager to learn", "honest_approach"),
                ]
            },
            "impress_boss": {
                "text": "You launch into a detailed explanation of your final year project on automated irrigation systems, throwing in technical terms like 'microcontroller interfacing' and 'sensor calibration.'\n\nMr. Danladi's expression gradually softens. 'Not bad, not bad. UniPort dey produce better engineers than I thought. You go work with Ibrahim on our smart home project.'",
                "image": "office",
                "options": [
                    ("Meet Ibrahim and the rest of the team", "meet_team"),
                ]
            },
            "honest_approach": {
                "text": "'Honestly, sir, I'm nervous but very eager to learn and contribute. UniPort gave me a solid foundation, but I know there's so much more to learn in the real world.'\n\nMr. Danladi nods approvingly. 'I like your honesty, corper. No worry, we go train you well. You go work with Ibrahim on our smart home project.'",
                "image": "office",
                "options": [
                    ("Meet Ibrahim and the rest of the team", "meet_team"),
                ]
            },
            "meet_team": {
                "text": "Ibrahim is a friendly engineer in his late twenties who immediately takes you under his wing. 'Welcome to Nascomsoft! Don't mind Oga, he likes to scare new people, but he's actually very supportive.'\n\nYou also meet Aisha (software developer), Mohammed (hardware specialist), and Fatima (project manager). They switch between English, Hausa, and tech jargon so quickly your head spins.",
                "image": "office",
                "options": [
                    ("Focus on understanding the technical aspects of your work", "technical_focus"),
                    ("Try to join the social conversation despite the language barrier", "social_focus"),
                ]
            },
            "technical_focus": {
                "text": "You focus on understanding the smart home project specifications. Ibrahim explains that you'll be working on a system that uses local materials and affordable technology to create smart homes adapted to Nigerian realities, including power outages and security concerns.\n\n'Your Mechatronics background is perfect for this,' Ibrahim says.",
                "image": "office",
                "options": [
                    ("Dive into the project documentation", "work_day_end"),
                ]
            },
            "social_focus": {
                "text": "You try to join the conversation as your colleagues switch to discussing weekend plans. You catch mentions of 'suya spot,' 'Yankari Game Reserve,' and something about a wedding.\n\nAisha notices your confusion and explains in English: 'We're planning a welcome outing for you this weekend. We'll take you to taste the best suya in Bauchi!'",
                "image": "office",
                "options": [
                    ("Thank them and accept the invitation", "work_day_end"),
                ]
            },
            "work_day_end": {
                "text": "Your first day ends with a clearer understanding of your role at Nascomsoft. As you prepare to leave, Mr. Danladi stops by.\n\n'How market, corper? You don settle?' he asks with unexpected informality.\n\nBefore you can answer, he continues: 'Tomorrow, come with your laptop. We get serious work.'",
                "image": "office",
                "options": [
                    ("Head home and prepare for tomorrow", "evening_choices"),
                ]
            },
            "evening_choices": {
                "text": f"Back at your apartment, you reflect on your first day. You've met new colleagues, gotten a glimpse of your work, and experienced a taste of Bauchi life. But there's still so much to learn and adapt to.\n\nIt's evening now, and you need to decide how to spend it.",
                "image": "apartment",
                "options": [
                    ("Study technical documentation for tomorrow", "study_tech"),
                    ("Try to learn more Hausa phrases online", "learn_hausa"),
                    ("Explore the neighborhood", "explore_neighborhood"),
                    ("Call your family in Port Harcourt", "call_family"),
                ]
            },
            "study_tech": {
                "text": "You spend the evening reviewing documentation on embedded systems and IoT architecture. The project at Nascomsoft seems challenging but exciting.\n\nAs you study, you realize how your university education prepared you for some aspects but left gaps in others. Nevertheless, you feel more confident about tomorrow.",
                "image": "apartment",
                "options": [
                    ("Go to sleep and prepare for the next day", "next_day"),
                ]
            },
            "learn_hausa": {
                "text": "You find a Hausa learning app and spend ₦500 on the premium version. You practice basic phrases:\n\n- Ina kwana? (How did you sleep?)\n- Kana lafiya? (Are you well?)\n- Ina son... (I want...)\n\nThe pronunciation is challenging, but you're determined to learn.",
                "image": "apartment",
                "options": [
                    ("Practice until you're tired and go to sleep", "next_day"),
                ]
            },
            "explore_neighborhood": {
                "text": "You decide to explore your neighborhood. The streets are lively with children playing, women selling food, and men gathered around discussing politics.\n\nA group of children spot you and excitedly shout 'Corper! Corper!' They follow you, asking for sweets or coins. An older man shoos them away, saying 'Bamu da kuɗi' (We don't have money).",
                "image": "bauchi",
                "options": [
                    ("Try to chat with the local shopkeepers", "meet_locals"),
                    ("Buy some local food for dinner", "buy_food"),
                    ("Head back to your apartment", "next_day"),
                ]
            },
            "meet_locals": {
                "text": "You stop at a small provision store. The shopkeeper, a middle-aged woman, greets you warmly.\n\n'Ah, new corper! Welcome-welcome. I be Mama Blessing. My pikin don serve for Abia State before. Una people treat am well-well, so I go treat you well too!'",
                "image": "market",
                "options": [
                    ("Chat with Mama Blessing about life in Bauchi", "make_friend"),
                    ("Buy some provisions and head home", "next_day"),
                ]
            },
            "buy_food": {
                "text": "You follow your nose to a suya spot where a man is grilling meat over an open flame. The aroma is irresistible.\n\n'Corper, come chop correct suya!' the vendor calls out. 'Bauchi suya better pass Port Harcourt own!'\n\nYou spend ₦1000 on a generous portion of spicy suya wrapped in newspaper and a cold soft drink.",
                "image": "food",
                "options": [
                    ("Enjoy your meal and head home", "next_day"),
                ]
            },
            "call_family": {
                "text": "You call your parents in Port Harcourt. Your mother answers immediately, bombarding you with questions:\n\n'Nna m, how far? You don reach? The place safe? You don chop? The weather how? You need make I send garri come?'\n\nYou spend an hour reassuring her that you're fine while your father occasionally interjects with practical advice.",
                "image": "apartment",
                "options": [
                    ("Finish the call and go to sleep", "next_day"),
                ]
            },
            "next_day": {
                "text": f"Day {self.day+1}: You wake up to another day in Bauchi. Your NYSC adventure continues as you adapt to your new environment, work on interesting projects at Nascomsoft, and navigate cultural differences.\n\nWhat will you focus on today?",
                "image": "apartment",
                "options": [
                    ("Head to work early to impress your boss", "work_focus"),
                    ("Stop by the market to experience more local culture", "market_visit"),
                    ("Find a Hausa tutor to improve your language skills", "find_tutor"),
                ]
            },
            "work_focus": {
                "text": "You arrive at Nascomsoft early, finding only Mr. Danladi already there. He nods approvingly.\n\n'Corper, you serious. I like that. Today, we get client meeting. Big opportunity for us. You go follow for meeting, but no talk unless I ask you, understand?'",
                "image": "office",
                "options": [
                    ("Prepare for the client meeting", "client_meeting"),
                    ("Work on your assigned tasks first", "regular_work"),
                ]
            },
            "client_meeting": {
                "text": "The client is a real estate developer looking to incorporate smart home features into a new housing estate. During the meeting, Mr. Danladi unexpectedly turns to you.\n\n'My engineer go explain the technical aspects,' he says, giving you the floor.\n\nPut on the spot, you take a deep breath and recall your university presentations...",
                "image": "office",
                "options": [
                    ("Give a confident technical explanation", "impress_client"),
                    ("Keep it simple and focus on practical benefits", "practical_approach"),
                ]
            },
            "impress_client": {
                "text": "You launch into a detailed explanation of IoT architecture, sensor networks, and power management systems. The client looks increasingly confused.\n\nMr. Danladi interrupts: 'What my young engineer is saying is that our system go work even when NEPA take light, and e go save you money for long run.'",
                "image": "office",
                "options": [
                    ("Let Mr. Danladi take over the conversation", "meeting_end"),
                ]
            },
            "practical_approach": {
                "text": "'Our system is designed specifically for Nigerian conditions,' you explain. 'It works during power outages, enhances security, and reduces electricity costs. Plus, homeowners can control everything from their phones.'\n\nThe client nods enthusiastically. Mr. Danladi gives you an approving glance.",
                "image": "office",
                "options": [
                    ("Continue the discussion with the client", "meeting_success"),
                ]
            },
            "meeting_success": {
                "text": "The meeting ends successfully with the client agreeing to a pilot project. As everyone leaves, Mr. Danladi pats your shoulder.\n\n'You do well, corper. Maybe UniPort no be waste of time after all,' he says with a rare smile. 'Tomorrow, you go follow Ibrahim go site for installation.'",
                "image": "office",
                "options": [
                    ("Thank Mr. Danladi and continue your work day", "work_day_end"),
                ]
            },
            "meeting_end": {
                "text": "The meeting concludes with the client showing interest but requesting a simplified proposal. After everyone leaves, Mr. Danladi pulls you aside.\n\n'Corper, you too technical. For Nigeria, we need simple-simple explanation. Customer no want hear big-big grammar. Next time, talk as if you dey explain to your mama, understand?'",
                "image": "office",
                "options": [
                    ("Apologize and promise to improve", "work_day_end"),
                ]
            },
            "market_visit": {
                "text": "You decide to visit the local market before heading to work. It's a sensory overload - colorful fabrics, aromatic spices, loud haggling in Hausa, and narrow pathways between stalls.\n\nA fabric seller calls out to you: 'Corper! Come buy fine material! Make I sew native for you. Bauchi style go make you fine pass!'",
                "image": "market",
                "options": [
                    ("Check out the fabrics", "buy_fabric"),
                    ("Look for food items instead", "food_shopping"),
                    ("Politely decline and head to work", "late_to_work"),
                ]
            },
            "buy_fabric": {
                "text": "The fabric seller shows you beautiful materials with intricate patterns. 'This one na special Bauchi design. If you wear am for office, even oga go respect you!'\n\nHe initially quotes ₦15,000, but after some hesitant haggling on your part, you get it for ₦8,000.",
                "image": "market",
                "options": [
                    ("Buy the fabric and head to work", "late_to_work"),
                ]
            },
            "food_shopping": {
                "text": "You browse food stalls, amazed at the variety of spices, grains, and vegetables you don't recognize. An elderly woman notices your confusion.\n\n'Corper, you want cook?' she asks in broken English. 'Make I show you correct ingredients for Miyan Taushe (Pumpkin soup).'",
                "image": "market",
                "options": [
                    ("Let her teach you about local ingredients", "cooking_lesson"),
                    ("Thank her but explain you need to get to work", "late_to_work"),
                ]
            },
            "cooking_lesson": {
                "text": "The woman, who introduces herself as Hajiya Maimuna, gives you an impromptu cooking lesson, explaining various spices and vegetables. She insists on giving you some pumpkin and spices for free.\n\n'You come learn our culture, na good thing. Tonight, you go cook Miyan Taushe!'",
                "image": "market",
                "options": [
                    ("Thank her and rush to work", "late_to_work"),
                ]
            },
            "late_to_work": {
                "text": "You arrive at work late, earning a stern look from Mr. Danladi.\n\n'Corper, you think say this na NYSC camp wey you go come anytime? For here, we dey serious. No be play-play.'",
                "image": "office",
                "options": [
                    ("Apologize and explain about the market", "market_excuse"),
                    ("Apologize without excuses and get to work", "work_hard"),
                ]
            },
            "market_excuse": {
                "text": "'Sorry sir, I was at the market trying to learn more about Bauchi culture and...'\n\nMr. Danladi interrupts: 'Market culture no go help our deadline! But...' his expression softens slightly, 'you buy anything good?'",
                "image": "office",
                "options": [
                    ("Show him what you bought", "share_purchase"),
                    ("Promise it won't happen again and get to work", "work_hard"),
                ]
            },
            "share_purchase": {
                "text": "You show Mr. Danladi your purchase. He examines it with unexpected interest.\n\n'Hmm, you get good eye for quality. My wife dey find this kind material since. Where you buy am?'\n\nYour market adventure unexpectedly becomes a conversation starter with your stern boss.",
                "image": "office",
                "options": [
                    ("Share details about the market vendor", "connect_with_boss"),
                ]
            },
            "connect_with_boss": {
                "text": "You tell Mr. Danladi about the market vendor. He nods approvingly.\n\n'That man na my wife brother cousin! Small world. Okay, today I go forgive your lateness, but make e no happen again. Now, go help Ibrahim with the prototype testing.'",
                "image": "office",
                "options": [
                    ("Thank him and get to work", "work_day_end"),
                ]
            },
            "work_hard": {
                "text": "You dive into your work, staying focused and productive. Ibrahim notices your dedication.\n\n'You dey try to impress oga, abi? No worry, him bark pass him bite. But good job on these sensor configurations.'",
                "image": "office",
                "options": [
                    ("Continue working diligently", "work_overtime"),
                    ("Ask Ibrahim for feedback on your work", "seek_feedback"),
                ]
            },
            "work_overtime": {
                "text": "You stay late at the office, fine-tuning the prototype. Mr. Danladi passes by on his way out.\n\n'Corper, you still dey? Dedication good, but no kill yourself o. Tomorrow na another day.'",
                "image": "office",
                "options": [
                    ("Finish up and head home", "next_day"),
                ]
            },
            "seek_feedback": {
                "text": "Ibrahim reviews your work carefully. 'You get good foundation, but for real-world application, we need consider power fluctuations and dust - plenty dust for Bauchi! Let me show you how we adapt foreign technology to Nigerian reality.'",
                "image": "office",
                "options": [
                    ("Learn from Ibrahim's practical experience", "learn_practical"),
                ]
            },
            "learn_practical": {
                "text": "Ibrahim shows you ingenious workarounds for common Nigerian challenges - backup power systems, dust-resistant enclosures, and heat management solutions.\n\n'For Nigeria, theory na 30%, practical experience na 70%. Book knowledge good, but local knowledge better!'",
                "image": "office",
                "options": [
                    ("Thank Ibrahim for the valuable lessons", "work_day_end"),
                ]
            },
            "find_tutor": {
                "text": "You ask around for a Hausa tutor and are directed to Mallam Suleiman, a retired schoolteacher who lives nearby. He agrees to teach you for ₦2,000 per week.\n\n'Hausa no hard like English,' he assures you. 'Small-small, you go dey speak like Bauchi person!'",
                "image": "apartment",
                "options": [
                    ("Start your first lesson", "hausa_lesson"),
                    ("Negotiate the price first", "negotiate_tutor"),
                ]
            },
            "hausa_lesson": {
                "text": "Mallam Suleiman is a patient teacher. He focuses on practical phrases:\n\n'Kina da ruwa?' (Do you have water?)\n'Ina son siyan...' (I want to buy...)\n'Nawa ne?' (How much?)\n\nHe makes you repeat each phrase until your pronunciation is passable.",
                "image": "apartment",
                "options": [
                    ("Practice diligently", "hausa_progress"),
                    ("Ask about cultural context", "cultural_lesson"),
                ]
            },
            "hausa_progress": {
                "text": "After an hour of practice, you can introduce yourself and ask basic questions in Hausa. Mallam Suleiman nods approvingly.\n\n'You learn fast! Next time, we go market together. You go practice with real people.'",
                "image": "apartment",
                "options": [
                    ("Thank him and head to work", "late_to_work"),
                ]
            },
            "cultural_lesson": {
                "text": "'Language na just small part,' Mallam Suleiman explains. 'For Hausa culture, respect very important. Always greet elders first. Men and women get different roles. When person give you something, collect with right hand only.'",
                "image": "apartment",
                "options": [
                    ("Ask more about local customs", "custom_lesson"),
                    ("Thank him and head to work", "late_to_work"),
                ]
            },
            "custom_lesson": {
                "text": "Mallam Suleiman explains various customs - removing shoes before entering certain places, the importance of Friday prayers for Muslims, traditional greetings for different times of day, and food etiquette.\n\n'These small-small things go make people accept you quick-quick,' he advises.",
                "image": "apartment",
                "options": [
                    ("Thank him for the valuable insights", "late_to_work"),
                ]
            },
            "negotiate_tutor": {
                "text": "'Mallam, ₦2,000 too much for corper wey just start work,' you attempt to negotiate. 'How about ₦1,000 per week?'\n\nMallam Suleiman laughs. 'Your negotiation need work! But because you want learn our language, I go accept ₦1,500. Final price!'",
                "image": "apartment",
                "options": [
                    ("Accept the offer and start your lesson", "hausa_lesson"),
                    ("Thank him but say you'll think about it", "late_to_work"),
                ]
            },
            "random_power_outage": {
                "text": "NEPA strikes again! The power goes out suddenly while you're in the middle of important work. The office generator kicks in after a few minutes, but your unsaved work is lost.\n\nIbrahim laughs at your frustration. 'First time? For here, we save work every two minutes. NEPA na our unofficial productivity manager!'",
                "image": "office",
                "options": [
                    ("Laugh it off and restart your work", "work_day_end"),
                    ("Ask about better backup solutions", "backup_discussion"),
                ]
            },
            "backup_discussion": {
                "text": "Your question sparks a lively office debate about the best power backup solutions. Everyone has an opinion:\n\n'Inverter better pass generator!'\n'Solar na the future!'\n'Nothing beat good old gen, just buy quality fuel!'\n\nMr. Danladi ends the debate: 'All this talk no dey bring light. Back to work!'",
                "image": "office",
                "options": [
                    ("Return to your tasks", "work_day_end"),
                ]
            },
            "random_invitation": {
                "text": "Fatima approaches you during lunch break. 'My brother dey do traditional wedding this weekend. You want come? Go be good experience for you to see Bauchi culture.'",
                "image": "office",
                "options": [
                    ("Accept the invitation enthusiastically", "accept_wedding"),
                    ("Politely decline due to work commitments", "decline_wedding"),
                ]
            },
            "accept_wedding": {
                "text": "'I'd love to come! Thank you for inviting me,' you reply.\n\nFatima beams. 'Nice one! Make sure you wear something colorful. And prepare your stomach - Bauchi wedding food plenty pass anything you don see for Port Harcourt!'",
                "image": "office",
                "options": [
                    ("Ask what gift would be appropriate", "wedding_gift"),
                    ("Ask what to expect at a traditional wedding", "wedding_customs"),
                ]
            },
            "wedding_gift": {
                "text": "'Gift? No worry yourself about that. You be visitor and corper. Your presence na gift already!' Fatima assures you. 'But if you want, you fit give small money inside envelope. Any amount wey your pocket allow.'",
                "image": "office",
                "options": [
                    ("Thank her for the information", "work_day_end"),
                ]
            },
            "wedding_customs": {
                "text": "Fatima explains the wedding customs - the henna night before the wedding, the bride's dramatic entrance, the traditional dances, and the elaborate feast.\n\n'And one more thing,' she adds with a smile, 'be ready to dance. Everybody must dance, no excuse!'",
                "image": "office",
                "options": [
                    ("Express concern about your dancing skills", "dance_worry"),
                    ("Look forward to the experience", "work_day_end"),
                ]
            },
            "dance_worry": {
                "text": "'Ah, I'm not sure about dancing...' you say hesitantly.\n\nFatima laughs. 'No worry! For Hausa dance, just raise your hands and move small-small. Nobody go judge you. In fact, if you dance bad, people go enjoy am pass!'",
                "image": "office",
                "options": [
                    ("Promise to give it your best try", "work_day_end"),
                ]
            },
            "decline_wedding": {
                "text": "You explain that you need to catch up on work. Fatima looks disappointed.\n\n'Work go always dey, but experience like this no come every time. Think again, corper!'",
                "image": "office",
                "options": [
                    ("Reconsider and accept", "accept_wedding"),
                    ("Stick to your decision", "miss_opportunity"),
                ]
            },
            "miss_opportunity": {
                "text": "The following Monday, the office is buzzing with stories and photos from the wedding. You feel a pang of regret as you see the colorful attires, elaborate food, and joyful celebrations you missed.\n\nIbrahim shakes his head. 'Corper, you miss big opportunity to connect with community o!'",
                "image": "office",
                "options": [
                    ("Promise to join next time", "work_day_end"),
                ]
            },
            "random_food": {
                "text": "Mohammed brings a container of food to the office. 'My wife cook too much Tuwo Shinkafa yesterday. Corper, come chop!'\n\nHe opens the container to reveal a white dough-like substance with a rich, spicy soup containing meat and vegetables.",
                "image": "food",
                "options": [
                    ("Try it enthusiastically", "enjoy_food"),
                    ("Take a small portion to be polite", "cautious_taste"),
                ]
            },
            "enjoy_food": {
                "text": "You dig in with enthusiasm. The Tuwo is bland but perfect for scooping up the flavorful soup. Despite the spiciness that makes your eyes water, you finish your portion.\n\nMohammed beams with pride. 'See as corper dey chop like Bauchi person! My wife go happy when I tell am!'",
                "image": "food",
                "options": [
                    ("Ask for the recipe", "recipe_request"),
                    ("Thank Mohammed for sharing", "work_day_end"),
                ]
            },
            "recipe_request": {
                "text": "Mohammed laughs heartily at your request. 'You want learn how to cook Tuwo? My wife go think say I want marry second wife! But okay, I go tell her teach you one day. Good skill for corper to know local food.'",
                "image": "food",
                "options": [
                    ("Look forward to the cooking lesson", "work_day_end"),
                ]
            },
            "cautious_taste": {
                "text": "You take a small portion and taste it carefully. The spiciness hits you immediately, making you cough. Everyone laughs good-naturedly.\n\n'Water dey that side!' Mohammed points, grinning. 'No worry, next time we go reduce pepper for you. Port Harcourt people no dey used to real pepper!'",
                "image": "food",
                "options": [
                    ("Drink water and thank Mohammed", "work_day_end"),
                ]
            },
            # Add more scenes as needed
        }
        
        # Get the current scene data
        scene_data = scenes.get(self.current_scene, {
            "text": "Scene not found. This is a placeholder.",
            "image": "nysc_logo",
            "options": [("Continue", "next_day")],
        })
        
        # Update the UI with the scene data
        self.update_story_text(scene_data["text"])
        self.set_image(scene_data["image"])
        self.create_option_buttons(scene_data["options"])

# Main function to run the game
def main():
    root = tk.Tk()
    game = NigerianAdventureGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
