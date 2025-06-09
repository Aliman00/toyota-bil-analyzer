from main import parse_car_data, client, fetch_car_data, finn_url as default_finn_url
import streamlit as st
import pandas as pd
import requests

st.set_page_config(layout="wide")
st.title("🚗 Bil data analysator og chatbot")

# --- Initialize session state ---
if 'raw_car_data_text' not in st.session_state:
    st.session_state.raw_car_data_text = None
if 'parsed_cars_list' not in st.session_state:
    st.session_state.parsed_cars_list = []
if 'current_finn_url' not in st.session_state:
    st.session_state.current_finn_url = default_finn_url
if "messages" not in st.session_state: # For chat history
    st.session_state.messages = []
if "initial_analysis_done" not in st.session_state: # To track if initial analysis was performed
    st.session_state.initial_analysis_done = False

# --- Data Fetching Section in Sidebar ---
st.sidebar.header("⚙️ Data Kilde")
user_finn_url = st.sidebar.text_input(
    "Skriv inn Finn.no URL:",
    value=st.session_state.current_finn_url,
    key="finn_url_input"
)

if st.sidebar.button("Hent og analyser nye data", type="primary"):
    st.session_state.current_finn_url = user_finn_url
    # Reset chat and analysis state when new data is fetched
    st.session_state.messages = []
    st.session_state.initial_analysis_done = False
    st.session_state.raw_car_data_text = None # Clear previous raw text
    st.session_state.parsed_cars_list = [] # Clear previous parsed list

    if st.session_state.current_finn_url:
        with st.spinner(f"Henter data fra {st.session_state.current_finn_url}..."):
            try:
                raw_text = fetch_car_data(st.session_state.current_finn_url)
                st.session_state.raw_car_data_text = raw_text
                st.sidebar.success("Data hentet!")
            except requests.exceptions.RequestException as e:
                st.sidebar.error(f"Feil ved henting av data: {e}")
            except Exception as e:
                st.sidebar.error(f"En uventet feil oppstod: {e}")

        if st.session_state.raw_car_data_text:
            with st.spinner("Parser data..."):
                try:
                    st.session_state.parsed_cars_list = parse_car_data(st.session_state.raw_car_data_text)
                except Exception as e:
                    st.sidebar.error(f"Feil ved parsing av data: {e}")
        else:
            if st.session_state.current_finn_url: # Only show this if a URL was provided but fetch failed
                st.sidebar.error("Henting feilet, kan ikke parse.")
    else:
        st.sidebar.warning("Vennligst skriv inn en URL for å hente data.")

# --- Display Parsed Data ---
st.header("📊 Bil Data")
if st.session_state.parsed_cars_list:
    df_cars = pd.DataFrame(st.session_state.parsed_cars_list)
    
    # Use 'original_chunk_order' if it exists (from car_data.py changes), otherwise 'id'
    index_column_to_use = None
    if 'original_chunk_order' in df_cars.columns:
        index_column_to_use = 'original_chunk_order'
    elif 'id' in df_cars.columns:
        index_column_to_use = 'id'

    if index_column_to_use:
        df_cars = df_cars.set_index(index_column_to_use)
    else:
        st.warning("Ingen passende ID-kolonne ('original_chunk_order' eller 'id') funnet. Bruker standardindeks.")

    if 'price' in df_cars.columns:
        df_cars['price_display'] = df_cars['price'].astype(str).replace('nan', 'N/A')
    else:
        df_cars['price_display'] = 'N/A'

    column_config = {
        "name": st.column_config.TextColumn("Model", width="large", help="Bil navn og variant."),
        "link": st.column_config.LinkColumn("Finn.no link", help="Direkte link til finn.no annonsen", display_text="Link", width="small"),
        "image_url": st.column_config.ImageColumn("Bilde", help="Bil bilde", width="medium"),
        "year": st.column_config.NumberColumn("Årsmodell", format="%d", help="Produksjonsår for bilen."),
        "mileage": st.column_config.NumberColumn("Kilometerstand", format="%d km", help="Antall kilometer bilen har kjørt."),
        "price_display": st.column_config.TextColumn("Pris", help="Pris i norske kroner (kr). 'Solgt' for solgte biler.", width="small"),
        "age": st.column_config.NumberColumn("Alder", format="%d år", help="Alder på bilen i år."),
        "km_per_year": st.column_config.NumberColumn("Kilometer/år", format="%d km", help="Gjennomsnittlig kilometerstand per år."),
    }
    
    desired_column_order = ["name", "year", "mileage", "price_display", "age", "km_per_year", "link", "image_url"]
    display_columns = [col for col in desired_column_order if col in df_cars.columns]

    st.data_editor(
        df_cars[display_columns],
        column_config=column_config,
        use_container_width=True,
        height=400,
        disabled=True
    )

    st.subheader("📈 Statistikk basert på innhentet data:")
    valid_prices = [car['price'] for car in st.session_state.parsed_cars_list if isinstance(car['price'], (int, float))]
    if valid_prices:
        avg_price = sum(valid_prices) / len(valid_prices)
        st.metric(label="Gjennomsnittlig pris ", value=f"{avg_price:,.0f} kr")

    valid_mileage = [car['mileage'] for car in st.session_state.parsed_cars_list if car['mileage'] is not None]
    if valid_mileage:
        avg_mileage = sum(valid_mileage) / len(valid_mileage)
        st.metric(label="Gjennomsnittlig kjørelengde", value=f"{avg_mileage:,.0f} km")

    sold_cars_count = sum(1 for car in st.session_state.parsed_cars_list if str(car.get('price', '')).lower() == "solgt")
    st.metric(label="Solgte biler", value=sold_cars_count)
else:
    st.info("Ingen bil data å vise. Bruk sidefeltet til å hente og analysere data fra Finn.no.") # This message will now show on startup

# --- AI Analysis & Chat Section ---
st.header("🤖 AI-analyse og chat")

# Button to trigger initial analysis
if st.button("🔍 Start AI Analysis with Current Data", disabled=not st.session_state.parsed_cars_list):
    if st.session_state.parsed_cars_list and st.session_state.raw_car_data_text:
        st.session_state.messages = [] # Clear previous chat
        st.session_state.initial_analysis_done = False # Reset flag

        initial_prompt_content = f"""Analyze the provided car data and present your findings.
        Parsed structured car data:
        {st.session_state.parsed_cars_list}

        Based on this data, provide the following insights in a clear, structured format:
        1.  Average price of cars (excluding 'Solgt').
        2.  Average mileage of cars.
        3.  Average age of cars.
        4.  Average km per year for cars.
        5.  Number of cars marked as 'Solgt'.

        After presenting these insights, offer recommendations for which car(s) to consider buying. Include a direct link to each recommended car's advertisement.
        Your recommendations should be based on:
            *   Good value (considering price vs. age/mileage).
            *   Low km/year (cars with less than 15,000 km/year are considered low mileage; over 20,000 km/year is high).
            *   Overall appeal, using general knowledge about Toyota models.

        This is the initial analysis. I may ask follow-up questions later.

        IMPORTANT: Your entire response must consist ONLY of the requested insights and recommendations. Do not include any introductory phrases, system messages, conversational filler, or repeat any part of this prompt or the raw data. Respond directly with the analysis.
        """
        
        st.session_state.messages.append({"role": "system", "content": (
            "You are an expert automotive analyst. Your primary function is to analyze car data and provide insights and recommendations. "
            "All responses must be in Norwegian. "
            "Present information using clear, well-structured markdown. "
            "Your entire response will consist *only* of the specific analysis and recommendations requested in the user's prompt. "
            "Under no circumstances should you include introductory phrases, system messages, conversational filler, apologies, or repeat any part of the input prompt or raw data. "
            "Respond directly with the analysis."
        )})
        # Add the initial user prompt with a flag to prevent it from being displayed
        st.session_state.messages.append({
            "role": "user",
            "content": initial_prompt_content,
            "is_hidden_prompt": True  # This flag will be used to hide it from the UI
        })

        with st.spinner("AI utfører innledende analyse ... dette kan ta litt tid..."):
            try:
                completion = client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324:free",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                )
                ai_response_content = completion.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": ai_response_content})
                st.session_state.initial_analysis_done = True # Set flag
            except Exception as e:
                st.error(f"An error occurred during initial AI analysis: {e}")
                # Remove the user prompt if AI fails, to prevent it from being displayed without a response
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()

    else:
        st.warning("Cannot start AI Analysis. Ensure data is fetched and parsed successfully.")

# Display chat messages
if st.session_state.messages:
    for message in st.session_state.messages:
        # Don't display system messages or the hidden initial prompt in the chat UI
        if message["role"] != "system" and not message.get("is_hidden_prompt", False):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# Chat input for follow-up questions
if st.session_state.initial_analysis_done: # Only allow chat if initial analysis is done
    if prompt := st.chat_input("Ask a follow-up question about the cars..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("AI is thinking..."):
            try:
                completion = client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324:free",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                )
                ai_response_content = completion.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": ai_response_content})
            except Exception as e:
                st.error(f"An error occurred during follow-up AI analysis: {e}")