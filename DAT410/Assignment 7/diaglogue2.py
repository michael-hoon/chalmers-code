import pandas as pd
import re
from datetime import datetime, timedelta

WEATHER_DF = pd.read_csv('weather_data.csv')
RESTAURANTS_DF = pd.read_csv('restaurant_data.csv')
TRANSPORT_DF = pd.read_csv('transport_data.csv')

class IntentRecognizer:
    """Handles intent detection with keyword matching and confidence scoring"""
    def __init__(self):
        self.intent_keywords = {
            'weather': ['weather', 'forecast', 'temperature', 'rain', 'snow', 'sunny', 'cloudy', 'humidity'],
            'restaurant': ['restaurant', 'eat', 'dinner', 'cuisine', 'food', 'menu'],
            'transport': ['tram', 'bus', 'transport', 'schedule', 'route', 'line'],
            'greeting': ['hello', 'hi', 'hey', 'heya', 'howdy', 'greetings'],
            'goodbye': ['bye', 'goodbye', 'exit', 'quit', 'farewell', 'see you'],
            'help': ['help', 'support', 'what can you do', 'what can you help me with']
        }

    def get_intent(self, text: str) -> str:
        text = text.lower()
        scores = {intent: 0 for intent in self.intent_keywords}
        
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                    scores[intent] += 1
                    
        max_intent = max(scores, key=scores.get)
        return max_intent if scores[max_intent] > 0 else None

class BaseTaskHandler:
    """Abstract base class for task handlers"""
    required_params = []
    
    def __init__(self, df):
        self.df = df
        self.missing_params = []
        
    def extract_parameters(self, text):
        raise NotImplementedError
        
    def get_response(self, params):
        raise NotImplementedError
        
    def handle(self, text):
        params = self.extract_parameters(text)
        missing = [p for p in self.required_params if p not in params]
        
        if missing:
            self.missing_params = missing
            return self._create_prompt()
            
        self.missing_params = []
        return self.get_response(params)
        
    def _create_prompt(self):
        prompts = {
            'city': "Which city are you interested in?",
            'date': "For which date?",
            'time': "What time are you looking for?",
            'cuisine': "What type of cuisine would you like?"
        }
        return "\n".join([prompts[p] for p in self.missing_params])

class WeatherHandler(BaseTaskHandler):
    required_params = ['city', 'date']
    
    def extract_parameters(self, text: str) -> dict:
        params = {}
        cities = '|'.join(WEATHER_DF['city'].unique())
        if match := re.search(fr'\b({cities})\b', text, re.I):
            params['city'] = match.group(1)
            
        if re.search(r'\btoday\b', text, re.I):
            params['date'] = datetime.now().strftime("%Y-%m-%d")
        elif re.search(r'\btomorrow\b', text, re.I):
            params['date'] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif match := re.search(r'\d{4}-\d{2}-\d{2}', text):
            params['date'] = match.group()
            
        return params
        
    def get_response(self, params):
        filtered = self.df[
            (self.df['city'] == params['city']) &
            (self.df['date'] == params['date'])
        ]
        if filtered.empty:
            return "No weather data available for that location and date"
            
        forecast = filtered.iloc[0]
        return (
            f"Weather forecast for {params['city']} on {params['date']}:\n"
            f"Temperature: {forecast['temperature_min']}°C to {forecast['temperature_max']}°C\n"
            f"Conditions: {forecast['condition']}\n"
            f"Humidity: {forecast['humidity']}%"
        )

class RestaurantHandler(BaseTaskHandler):
    required_params = ['city', 'cuisine']
    
    def extract_parameters(self, text):
        params = {}
        cities = '|'.join(RESTAURANTS_DF['city'].unique())
        cuisines = '|'.join(RESTAURANTS_DF['cuisine'].unique())
        
        if match := re.search(fr'\b({cities})\b', text, re.I):
            params['city'] = match.group(1)
            
        if match := re.search(fr'\b({cuisines})\b', text, re.I):
            params['cuisine'] = match.group(1)
            
        return params
        
    def get_response(self, params):
        filtered = self.df[
            (self.df['city'] == params['city']) &
            (self.df['cuisine'] == params['cuisine'])
        ].sort_values('rating', ascending=False)
        
        if filtered.empty:
            return "No restaurants found matching your criteria"
            
        top_3 = filtered.head(3)
        response = [f"Top {params['cuisine']} restaurants in {params['city']}:"]
        for _, row in top_3.iterrows():
            response.append(
                f"- {row['name']} ({row['price_range']}), Rating: {row['rating']}/5"
            )
        return "\n".join(response)

class TransportHandler(BaseTaskHandler):
    required_params = ['city', 'time']
    
    def extract_parameters(self, text):
        params = {}
        cities = '|'.join(TRANSPORT_DF['city'].unique())

        # Extract city
        if not params.get('city'):
            if match := re.search(fr'\b({cities})\b', text, re.I):
                params['city'] = match.group(1)

        # Extract time with date awareness
        current_time = datetime.now()
        if not params.get('time'):
            # Handle relative time expressions
            if re.search(r'\btomorrow\b', text, re.I):
                # Transport data doesn't have dates, so we'll use current time
                params['time'] = "00:00"
                text = text.replace("tomorrow", "")  # Remove to avoid confusion
            elif re.search(r'\bnext hour\b', text, re.I):
                params['time'] = (current_time + timedelta(hours=1)).strftime("%H:%M")
            elif match := re.search(r'\b(\d{1,2})(:\d{2})?\s*(am|pm)?\b', text, re.I):
                hour = match.group(1)
                minute = match.group(2)[1:] if match.group(2) else "00"
                period = match.group(3).lower() if match.group(3) else ""
                # Convert to 24-hour format
                hour = int(hour)
                if period == 'pm' and hour < 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                params['time'] = f"{hour:02d}:{minute}"
            
        return params
        
    def get_response(self, params):
        # Handle "tomorrow" special case
        if params.get('time') == "00:00":
            return ("I can only show today's schedule. "
                    "Please specify a time (e.g. '14:30' or '2pm').")

        try:
            query_time = datetime.strptime(params['time'], "%H:%M").time()
        except ValueError:
            return "Please specify a valid time format (e.g. '14:30' or '2pm')."

        filtered = self.df[
            (self.df['city'] == params['city']) &
            (pd.to_datetime(self.df['departure_time'] >= params['time']))
        ].sort_values('departure_time')

        if filtered.empty:
            return "No upcoming transports found"
            
        next_3 = filtered.head(3)
        response = [f"Upcoming transports in {params['city']} from {params['time']}:"]
        for _, row in next_3.iterrows():
            response.append(
                f"- {row['type'].title()} {row['route']} departs at {row['departure_time']} "
                f"from {row['from_stop']} to {row['to_stop']}"
            )
        return "\n".join(response)

class ChatBot:
    """Main chatbot class managing conversation flow"""
    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.active_handler = None
        self.handlers = {
            'weather': WeatherHandler(WEATHER_DF),
            'restaurant': RestaurantHandler(RESTAURANTS_DF),
            'transport': TransportHandler(TRANSPORT_DF)
        }
        
    def handle_input(self, text):
        # Check for conversation termination
        if self.intent_recognizer.get_intent(text) == 'help':
            return ("I can help with:\n"
                    "- Weather forecasts (e.g. 'weather in Paris tomorrow')\n"
                    "- Restaurant recommendations (e.g. 'Italian food in London')\n"
                    "- Transport schedules (e.g. 'next bus in Berlin at 15:00')")

        # if self.intent_recognizer.get_intent(text) == 'goodbye':
        #     return "Goodbye! Have a nice day!"
            
        # Handle active conversation context
        if self.active_handler:
            response = self.active_handler.handle(text)
            if not self.active_handler.missing_params:
                self.active_handler = None
            return response
                
        # Detect new intent
        intent = self.intent_recognizer.get_intent(text)
        if not intent or intent not in self.handlers:
            return "I can help with weather, restaurants, and transport info. How can I assist you?"
            
        self.active_handler = self.handlers[intent]
        return self.active_handler.handle(text)

# Usage example
if __name__ == "__main__":
    bot = ChatBot()
    print("Chatbot: Hi! I'm your friendly assistant for today! I can help with weather forecasts, restaurant recommendations, and transport schedules. Ask me anything!")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("Chatbot: Goodbye! Have a nice day!")
            break
            
        response = bot.handle_input(user_input)
        print(f"Chatbot: {response}")