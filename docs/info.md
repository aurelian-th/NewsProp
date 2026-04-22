# Project Information & Methodology: NewsProp

## 1. What Exactly Does This Project Do?
Simply put: **It treats a piece of news like a biological virus and simulates a pandemic.**

Instead of coughing on people, agents "infect" their followers with information. Instead of a biological immune system fighting off a pathogen, the network's defense is "critical thinking." The project aims to mathematically simulate the spread of information—both real and fake—across a localized digital ecosystem (the Republic of Moldova) to prove concepts about how misinformation propagates and how it can be stopped.

## 2. How It Works (The 4 Steps)
1. **The Data:** It processes thousands of real articles parsed from the Moldovan digital space (`stiri.md` for real news, `stopfals.md` for fake news, and Telegram for alternative media).
2. **The AI:** It reads the headline and text using Natural Language Processing (NLP) to score exactly how "angry", "sad", or "provocative" it is using VADER Sentiment Analysis. The higher the emotional intensity, the better the news spreads.
3. **The Society:** It generates a synthetic social media graph using the Barabási–Albert model. This scale-free graph mimics real digital societies: ~5% of the nodes are "Influencers" (Hubs) with hundreds of connections, while 95% are regular users with only a few friends.
4. **The Simulation:** It injects an article into the network (Patient Zero) and hits "Play." Ticks (time steps) go by, probability math is calculated, and you can watch the geometric explosion of the idea propagating through the network's echo chambers based on the SEIZ epidemiological model.

## 3. The "Simulate as Fake News" Checkbox: Is it cheating?
It might feel like "cheating" to explicitly tell the simulation that a custom article is fake. Technically, a piece of text doesn't *know* it is fake. However, this toggles two scientifically proven phenomena:

* **The Virality Bonus:** A massive 2018 MIT study analyzed 126,000 stories on Twitter and found that **fake news naturally travels 6 times faster than the truth.** Fake news is artificially engineered for novelty and surprise. The checkbox adds a slight mathematical modifier to the transmission rate ($\beta$) to simulate algorithmic amplification and human novelty bias that basic NLP might miss.
* **The Skepticism Trigger:** In our SEIZ model, people can become "Skeptics" ($Z$). If a piece of news is true, agents generally accept it based on standard believability. If it is *fake*, agents with high `critical_thinking` stats will roll a mathematical "save" to realize it's a lie. They then turn into firewalls (Skeptics) that refuse to share it. The system needs to know the underlying truth of the article to know how the network's "immune system" should act.

## 4. Understanding the Network Map
When you run a simulation, you get a complex web of dots and lines representing the social state at the end of the timeline:
* **Dots (Nodes):** These are individual people (or accounts) in the synthetic Moldovan social network.
* **Lines (Edges):** These are follow/friend connections representing who interacts with whom.
* **Colors (SEIZ Model States):**
    * 🩶 **Gray (Susceptible):** Has not seen the news yet.
    * 🟧 **Orange (Exposed):** Saw the news on their feed, currently considering whether to trust it.
    * 🟥 **Red (Infected):** Emotion beat average critical thinking. They believe the news and are actively spreading/sharing it directly to their connections.
    * 🟩 **Green (Skeptic):** Critical thinking beat emotion. They recognized it as fake (or found it boring if it's real news), refusing to share it, acting as a dead-end firewall.

## 5. Is This Useful? (The Real-World Application)
Beyond academic research, this solves the "whack-a-mole" problem of social media moderation. 
This simulation proves a concept called **Targeted Pre-bunking**. By using the UI and checking **"Apply Pre-bunking (Immunize Hubs)"**, the code identifies the top 5% most connected nodes (the influencers) and forces them to a Green/Skeptic state at tick 0 before the fake news hits them.

Running this proves mathematically that by educating or warning just 5% of a network's major hubs, you can suffocate a viral fake news outbreak before it ever reaches the wider public.

## 6. How to Run the Dashboard
To start the final Phase 5 interface:

1. Open a terminal in the root of the project.
2. Ensure you have the UI requirements installed:
   ```bash
   pip install -r requirements-ui.txt -r requirements-phase45.txt
   ```
3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
4. A browser window will automatically open showing the interactive dashboard. You can search against scraped articles, or use the "Custom Article" mode to test your own hypothetical headlines.