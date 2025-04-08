import streamlit as st
import mysql.connector
import tempfile
import pandas as pd
from PIL import Image
import google.generativeai as genai
import base64
import os
import dotenv
dotenv.load_dotenv()
# --- CONFIG ---
st.set_page_config(page_title="Car-Quest ✨", layout="wide")

# --- STYLE ---
st.markdown("""
<style>
    .main { background-color: #f5f7fa; padding: 20px; }
    .title-style { font-size: 3em; color: #0a3d62; text-align: center; margin-bottom: 1em; }
    .sidebar .sidebar-content { background-color: #dff9fb; }
    .stButton>button { background-color: #0a3d62; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Home", "QuestAI", "Filters", "Compare"])

# --- SSL CERTIFICATE SETUP ---
ssl_ca_content = os.getenv("AIVEN_CA_PEM")

with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".pem") as tmp_file:
    tmp_file.write(ssl_ca_content)
    ssl_ca_path = tmp_file.name

# --- DB CONNECTION FUNCTION ---
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=int(os.getenv("MYSQL_PORT")),
        ssl_ca=ssl_ca_path,
        connection_timeout=30,
        use_pure=True
    )
    return conn

def bool_to_label(val):
    """Converts 1/0 (or True/False) to a user-friendly 'True'/'False'."""
    if val in [1, True]:
        return "True"
    elif val in [0, False]:
        return "False"
    return str(val)  # Fallback for other data types

# --- SQL GENERATION USING GEMINI ---
genai.configure(api_key=os.getenv("PPI"))
model = genai.GenerativeModel("gemini-1.5-flash")

def convert_to_sql(user_query):
    prompt = f'''
You are an expert SQL generator specializing in vehicle databases. Translate the following natural language query into MySQL queries using the provided schema.

Database: defaultdb

Schema definitions
# Vehicle table (basic info)
create_vehicle_table = """
CREATE TABLE IF NOT EXISTS Vehicle (
  vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
  brand VARCHAR(50) NOT NULL,
  model VARCHAR(50) NOT NULL,
  variant VARCHAR(255),
  type VARCHAR(50),
  price DECIMAL(20,2),
  url VARCHAR(255),
  image_link VARCHAR(255)
);
"""

# Engine table (engine details)
create_engine_table = """
CREATE TABLE IF NOT EXISTS Engine (
  engine_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  fuel VARCHAR(20),
  displacement INT,
  no_of_cylinders FLOAT,
  bhp_value INT,
  bhp_rpm FLOAT,
  torque_value FLOAT,
  torque_rpm FLOAT,
  FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
);
"""

# Transmission table (transmission details)
create_transmission_table = """
CREATE TABLE IF NOT EXISTS Transmission (
  transmission_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  transmission VARCHAR(50),
  gearbox INT,
  drive_type VARCHAR(50),
  FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
);
"""

# Performance table (mileage and capacity)
create_performance_table = """
CREATE TABLE IF NOT EXISTS Performance (
  performance_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  mileage FLOAT,
  capacity FLOAT,
  FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
);
"""

# Dimensions table (boot space, seating capacity, wheel base)
create_dimensions_table = """
CREATE TABLE IF NOT EXISTS Dimensions (
  dimension_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  boot_space FLOAT,
  seating_capacity INT,
  wheel_base FLOAT,
  FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
);
"""

# Chassis table (brakes and tyre details)
create_chassis_table = """
CREATE TABLE IF NOT EXISTS Chassis (
  chassis_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  front_brake VARCHAR(50),
  rear_brake VARCHAR(50),
  tyre_size VARCHAR(50),
  tyre_type VARCHAR(50),
  FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
);
"""

# Features table (additional features as booleans and extras)
create_features_table = """
CREATE TABLE IF NOT EXISTS Features (
  feature_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  cruise_control BOOLEAN,
  parking_sensors VARCHAR(20),
  keyLess_entry BOOLEAN,
  engine_start_stop_button BOOLEAN,
  LED_headlamps BOOLEAN,
  no_of_airbags INT,
  rear_camera BOOLEAN,
  hill_assist BOOLEAN,
  FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
);
"""

# Price table (separate table for per-city prices)
create_price_table = """
CREATE TABLE IF NOT EXISTS Price (
  price_id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  city VARCHAR(50) NOT NULL,
  price DECIMAL(20,2),
  FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
);


Now convert the following query to SQL:
"{user_query}"
    '''
    response = model.generate_content(prompt)
    sql_output = response.text
    return sql_output.split('```')[1][4:] if '```sql' in sql_output else sql_output

# --- EXPORT FUNCTION ---
def export_to_csv(data):
    csv = data.to_csv(index=False).encode('utf-8')
    b64 = base64.b64encode(csv).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="car_results.csv">Download CSV File</a>'
    st.markdown(href, unsafe_allow_html=True)

# --- HELPER FUNCTION: FETCH DETAILED VEHICLE INFO ---
def get_vehicle_details(vehicle_id):
    """
    This query may return multiple rows if the vehicle has multiple city-price entries.
    We will pivot or separate city/price data so we don't get repeated info in the other tabs.
    """
    query = f"""
    SELECT v.vehicle_id,
           v.brand, v.model, v.variant, v.type, v.price AS base_price,
           e.fuel, e.displacement, e.no_of_cylinders, e.bhp_value, e.bhp_rpm, e.torque_value, e.torque_rpm,
           t.transmission, t.gearbox, t.drive_type,
           pf.mileage, pf.capacity,
           d.boot_space, d.seating_capacity, d.wheel_base,
           c.front_brake, c.rear_brake, c.tyre_size, c.tyre_type,
           f.cruise_control, f.parking_sensors, f.keyLess_entry, f.engine_start_stop_button, f.LED_headlamps,
           f.no_of_airbags, f.rear_camera, f.hill_assist,
           p.city, p.price AS city_price
    FROM Vehicle v
    LEFT JOIN Engine e ON v.vehicle_id = e.vehicle_id
    LEFT JOIN Transmission t ON v.vehicle_id = t.vehicle_id
    LEFT JOIN Performance pf ON v.vehicle_id = pf.vehicle_id
    LEFT JOIN Dimensions d ON v.vehicle_id = d.vehicle_id
    LEFT JOIN Chassis c ON v.vehicle_id = c.vehicle_id
    LEFT JOIN Features f ON v.vehicle_id = f.vehicle_id
    LEFT JOIN Price p ON v.vehicle_id = p.vehicle_id
    WHERE v.vehicle_id = {vehicle_id}
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if not rows:
            return None

        # Convert to DataFrame
        df = pd.DataFrame(rows)

        # Separate city/price data from the rest
        # (1) vehicle_info: columns that are the same for each row
        # (2) city_prices: multiple city entries
        city_prices = df[['city','city_price']].drop_duplicates()
        vehicle_info = df.drop(columns=['city','city_price']).drop_duplicates(subset=['vehicle_id'])

        # Return them in a dictionary
        return {
            "vehicle_info": vehicle_info.reset_index(drop=True),
            "city_prices": city_prices.reset_index(drop=True)
        }
    except Exception as e:
        st.error(f"Error fetching details for vehicle {vehicle_id}: {e}")
        return None

# --- HELPER FUNCTION: FETCH SIMILAR CARS ---
def get_similar_cars(brand, vehicle_id, limit=3):
    """
    Example: fetch up to 3 other cars of the same brand, ignoring the current vehicle_id.
    Customize as needed for a more advanced recommendation.
    """
    query = f"""
    SELECT vehicle_id, brand, model, variant, type, image_link
    FROM Vehicle
    WHERE brand = '{brand}'
      AND vehicle_id <> {vehicle_id}
    LIMIT {limit}
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        st.error(f"Error fetching similar cars: {e}")
        return []

# --- PAGE: HOME ---
if page == "Home":
    # Hero Section
    st.markdown("""
        <style>
        .hero {
            background-color: #f0f2f6;
            padding: 2rem;
            border-radius: 1rem;
            text-align: center;
        }
        .hero h1 {
            font-size: 3rem;
            color: #f63366;
        }
        .hero p {
            font-size: 1.2rem;
            color: #333333;
        }
        </style>
        <div class="hero">
            <h1>🚘 CarQuest</h1>
            <p>Explore. Compare. Discover the best cars in India.</p>
        </div>
    """, unsafe_allow_html=True)

    # st.image(
    #     "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaxbUUFuNP8A3uA4z8k8uI2rRufeLha5qatQ&s",
    #     use_column_width=True,
    #     caption="Drive into the future with confidence."
    # )

    st.markdown("---")

    # Explore Section
    st.subheader("🔍 Explore Cars by Category")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.image("https://media.istockphoto.com/id/1167555914/photo/modern-red-suv-car-in-garage-with-lights-turned-on.jpg?s=612x612&w=0&k=20&c=DRKL152y8f0nxgcF-jfLAwM69YtcsYt86XHDEnCssI0=", caption="SUVs")
    with col2:
        st.image("https://media.istockphoto.com/id/1264045166/photo/car-driving-on-a-road.jpg?s=612x612&w=0&k=20&c=vRYLFjs6XMBZv0rl6Pbk77AlZvFe9RC6gSZuqUe_jXs=", caption="Sedans")
    with col3:
        st.image("https://media.istockphoto.com/id/1486018004/photo/a-happy-handsome-adult-male-charging-his-expensive-electric-car-before-leaving-his-house-for.jpg?s=612x612&w=0&k=20&c=rY6SHolsHcNtS_y23F0DgAe0arV6KZ_c3-k9r7PNP9Q=", caption="Electric Cars")

    st.markdown("---")

    # Top Picks Section
    st.subheader("🌟 Top Picks This Month")
    st.markdown("""
    - 🥇 **Hyundai Creta 2024** - Best Overall SUV
    - 🥈 **Tata Nexon EV** - Top Electric Car Under ₹15L
    - 🥉 **Honda City Hybrid** - Premium Sedan Choice
    - 🚀 **Maruti Fronx** - Value for Money Crossover
    """)

    st.markdown("---")

    # Knowledge Base Section
    st.subheader("🧠 Car Buying Guide & Resources")
    with st.expander("🚗 How to Choose the Right Car"):
        st.write("""
            Consider your needs: City vs Highway, Fuel type, Boot space, Safety features, and of course, Budget.
        """)
    with st.expander("⚡ EV vs Petrol vs Diesel"):
        st.write("""
            EVs are cost-effective in the long run and environment-friendly. Petrol cars are ideal for city use, diesel for longer distances.
        """)
    with st.expander("💰 Understanding Car Pricing"):
        st.write("""
            On-road price includes ex-showroom price, RTO charges, insurance, and optional accessories.
        """)

    st.markdown("---")

    # Articles & Trends
    st.subheader("📰 Trending Articles")
    st.markdown("""
    - 🚗 [Top Cars Under ₹10 Lakhs](https://www.autocarindia.com/)
    - 🔋 [Best Mileage Electric Vehicles](https://www.carwale.com/)
    - 🛠️ [Top 10 Reliable Cars in India](https://www.team-bhp.com/)
    - 🌐 [Upcoming Car Launches 2025](https://www.zigwheels.com/)
    """)

    st.markdown("---")

    # Teaser for Comparison Tool
    st.markdown("### 🆚 Ready to Compare?")
    st.info("Head to the **Compare** tab in the sidebar to see detailed specs and pricing of your favorite models!")

    # Future Scope/CTA
    st.markdown("---")
    st.subheader("💬 Coming Soon...")
    st.markdown("We're working on:")
    st.markdown("""
    - 🤖 AI-Powered Car Suggestion Bot
    - 🗺️ Location-Based Price Estimator
    - 📊 Ownership Cost Calculator
    - 🧾 EMI Planning Tool
    """)

    st.success("CarQuest is your all-in-one car discovery companion. Stay tuned!")

# --- PAGE: ASK IN ENGLISH ---
elif page == "QuestAI":
    st.subheader("QuestAI 💕")
    user_input = st.text_input("Ask me to find a car:")
    if st.button("Search"):
        if user_input:
            with st.spinner("Processing your request..."):
                mysql_query = convert_to_sql(user_input)
                st.code(mysql_query, language='sql')
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(mysql_query)
                    results = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    if results:
                        st.success("Results:")
                        df = pd.DataFrame(results)
                        st.dataframe(df)
                        export_to_csv(df)
                    else:
                        st.warning("No results found for your query.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please enter a query.")

# --- PAGE: CUSTOM FILTERS ---
elif page == "Filters":
    st.subheader("Filter Your Search")
    # Basic Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        city = st.selectbox(
            "Select City",
            options=["Ahmedabad", "Bangalore", "Chandigarh", "Chennai", "Hyderabad",
                     "Jaipur", "Lucknow", "Mumbai", "Patna", "Pune"]
        )
    with col2:
        brand = st.multiselect("Select Brand", options=["Maruti", "Hyundai", "Tata", "Toyota"])
    with col3:
        car_type = st.multiselect(
            "Select Car Type",
            options=["Sedan Cars", "Hatchback Cars", "SUV Cars", "MPV Cars"]
        )

    variant = st.text_input("Variant (Optional)")
    price_range = st.slider("Price Range (in Lakhs)", 0, 150, (5, 50))

    # Advanced Filters (Expandable)
    with st.expander("Advanced Filters"):
        fuel = st.multiselect("Fuel Type", options=["Petrol", "Diesel", "CNG", "Electric"])
        displacement_range = st.slider("Engine Displacement (cc)", 800, 5000, (800, 5000))
        bhp_range = st.slider("BHP Value", 50, 500, (50, 500))
        torque_range = st.slider("Torque Value (Nm)", 50, 5000, (50, 5000))
        mileage_range = st.slider("Mileage (kmpl)", 5, 40, (5, 40))
        seating_capacity = st.multiselect("Seating Capacity", options=[2, 4, 5, 7])
        transmission_type = st.multiselect("Transmission", options=["Manual", "Automatic"])
        sort_by = st.radio("Sort Results By", options=["Price", "BHP", "Mileage"], index=0)

    # Build filter conditions
    filters = []
    filters.append(f"p.city = '{city}'")
    filters.append(f"p.price BETWEEN {price_range[0]*100000} AND {price_range[1]*100000}")
    if brand:
        filters.append("v.brand IN (" + ", ".join(f"'{b}'" for b in brand) + ")")
    if car_type:
        filters.append("v.type IN (" + ", ".join(f"'{ct}'" for ct in car_type) + ")")
    if variant:
        filters.append(f"v.variant LIKE '%{variant}%'")
    if fuel:
        filters.append("e.fuel IN (" + ", ".join(f"'{f}'" for f in fuel) + ")")
    filters.append(f"e.displacement BETWEEN {displacement_range[0]} AND {displacement_range[1]}")
    filters.append(f"e.bhp_value BETWEEN {bhp_range[0]} AND {bhp_range[1]}")
    filters.append(f"e.torque_value BETWEEN {torque_range[0]} AND {torque_range[1]}")
    filters.append(f"pf.mileage BETWEEN {mileage_range[0]} AND {mileage_range[1]}")
    if seating_capacity:
        filters.append("d.seating_capacity IN (" + ", ".join(str(s) for s in seating_capacity) + ")")
    if transmission_type:
        filters.append("t.transmission IN (" + ", ".join(f"'{t}'" for t in transmission_type) + ")")

    where_clause = " AND ".join(filters)

    # Sorting clause
    sort_clause = {
        "Price": "p.price ASC",
        "BHP": "e.bhp_value DESC",
        "Mileage": "pf.mileage DESC"
    }.get(sort_by, "p.price ASC")

    final_query = f"""
      SELECT DISTINCT
          v.vehicle_id,
          v.brand,
          v.model,
          v.variant,
          v.type,
          p.price,
          v.image_link,
          e.bhp_value,
          pf.mileage
      FROM Vehicle v
      JOIN Price p ON v.vehicle_id = p.vehicle_id
      JOIN Engine e ON v.vehicle_id = e.vehicle_id
      JOIN Transmission t ON v.vehicle_id = t.vehicle_id
      JOIN Performance pf ON v.vehicle_id = pf.vehicle_id
      JOIN Dimensions d ON v.vehicle_id = d.vehicle_id
      JOIN Features f ON v.vehicle_id = f.vehicle_id
      WHERE {where_clause}
      ORDER BY {sort_clause}
      LIMIT 10
    """

    st.code(final_query, language='sql')

    # Execute query and display results
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(final_query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if results:
            df_results = pd.DataFrame(results)
            st.success("Matching Cars:")
            st.dataframe(df_results)
            export_to_csv(df_results)
            # Display detailed view for each result
            for _, car in df_results.iterrows():
                with st.container():
                    st.markdown(f"### {car['variant']} ({car['type']})")
                    cols = st.columns([1, 2])
                    with cols[0]:
                        st.image(car["image_link"], width=250)
                    with cols[1]:
                        st.markdown(f"**Price:** ₹{int(car['price']):,}")
                        details_data = get_vehicle_details(car["vehicle_id"])

                        if details_data is not None:
                            vehicle_info = details_data["vehicle_info"]
                            city_prices = details_data["city_prices"]

                            # Create tabs
                            tabs = st.tabs([
                                "Overview",
                                "Engine",
                                "Transmission",
                                "Performance",
                                "Dimensions & Chassis",
                                "Features",
                                "City Prices",
                                "Similar Cars"
                            ])

                            # We only need the first row for general details
                            # because we dropped duplicates on vehicle_id
                            row = vehicle_info.iloc[0]

                            # In your "Overview" tab:
                            with tabs[0]:
                                st.markdown("### Overview")
                                overview_dict = {
                                    "Brand": row['brand'],
                                    "Model": row['model'],
                                    "Variant": row['variant'],
                                    "Type": row['type'],
                                    "Base Ex-Showroom Price": f"₹{int(float(row['base_price'])):,}",
                                }
                                overview_df = pd.DataFrame(list(overview_dict.items()), columns=["Specification", "Value"])
                                st.table(overview_df)

                                # EMI example (if you want to keep it)
                                st.write("**Estimated EMI (5-year loan @ 8% APR):**")
                                principal = float(row['base_price'])  # cast decimal.Decimal to float
                                interest_rate_annual = 0.08
                                monthly_interest = interest_rate_annual / 12
                                months = 5 * 12
                                emi = (principal * monthly_interest) / (1 - (1 + monthly_interest) ** (-months))
                                st.write(f"Approx: ₹{int(emi):,} per month")

                            # In your "Engine" tab:
                            with tabs[1]:
                                st.markdown("### Engine")
                                engine_dict = {
                                    "Fuel": row['fuel'],
                                    "Displacement (cc)": row['displacement'],
                                    "No. of Cylinders": row['no_of_cylinders'],
                                    "BHP Value": row['bhp_value'],
                                    "BHP RPM": row['bhp_rpm'],
                                    "Torque Value (Nm)": row['torque_value'],
                                    "Torque RPM": row['torque_rpm']
                                }
                                engine_df = pd.DataFrame(list(engine_dict.items()), columns=["Specification", "Value"])
                                st.table(engine_df)

                            # In your "Transmission" tab:
                            with tabs[2]:
                                st.markdown("### Transmission")
                                transmission_dict = {
                                    "Transmission": row['transmission'],
                                    "Gearbox": row['gearbox'],
                                    "Drive Type": row['drive_type']
                                }
                                trans_df = pd.DataFrame(list(transmission_dict.items()), columns=["Specification", "Value"])
                                st.table(trans_df)

                            # In your "Performance" tab:
                            with tabs[3]:
                                st.markdown("### Performance")
                                perf_dict = {
                                    "Mileage (kmpl)": row['mileage'],
                                    "Fuel Tank Capacity (L)": row['capacity']
                                }
                                perf_df = pd.DataFrame(list(perf_dict.items()), columns=["Specification", "Value"])
                                st.table(perf_df)

                            # In your "Dimensions & Chassis" tab:
                            with tabs[4]:
                                st.markdown("### Dimensions & Chassis")
                                dim_chassis_dict = {
                                    "Boot Space (L)": row['boot_space'],
                                    "Seating Capacity": row['seating_capacity'],
                                    "Wheel Base (mm)": row['wheel_base'],
                                    "Front Brake": row['front_brake'],
                                    "Rear Brake": row['rear_brake'],
                                    "Tyre Size": row['tyre_size'],
                                    "Tyre Type": row['tyre_type']
                                }
                                dim_df = pd.DataFrame(list(dim_chassis_dict.items()), columns=["Specification", "Value"])
                                st.table(dim_df)

                            # In your "Features" tab:
                            with tabs[5]:
                                st.markdown("### Features")
                                features_dict = {
                                    "Cruise Control": bool_to_label(row['cruise_control']),
                                    "Parking Sensors": row['parking_sensors'] if row['parking_sensors'] else "None",
                                    "Keyless Entry": bool_to_label(row['keyLess_entry']),
                                    "Engine Start/Stop": bool_to_label(row['engine_start_stop_button']),
                                    "LED Headlamps": bool_to_label(row['LED_headlamps']),
                                    "No. of Airbags": row['no_of_airbags'] if row['no_of_airbags'] else "N/A",
                                    "Rear Camera": bool_to_label(row['rear_camera']),
                                    "Hill Assist": bool_to_label(row['hill_assist'])
                                }
                                feat_df = pd.DataFrame(list(features_dict.items()), columns=["Feature", "Value"])
                                st.table(feat_df)

                            # In your "City Prices" tab:
                            with tabs[6]:
                                st.markdown("### City Prices")
                                st.dataframe(city_prices)  # Or st.table(city_prices) if you prefer a static table

                            # In your "Similar Cars" tab (tabs[7]):
                            with tabs[7]:
                                st.write("**Similar Cars**")
                                similar = get_similar_cars(row['brand'], row['vehicle_id'], limit=3)
                                if similar:
                                    sim_cols = st.columns(len(similar))
                                    for i, sim_car in enumerate(similar):
                                        with sim_cols[i]:
                                            st.image(sim_car["image_link"], width=150)
                                            st.write(f"{sim_car['brand']} {sim_car['model']}")
                                            st.write(sim_car['variant'])
                                else:
                                    st.write("No similar cars found.")
                        else:
                            st.info("Detailed information not available.")
        else:
            st.warning("No results found.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

elif page == "Compare":
    st.title("📊 Compare Two Car Models")

    brand1 = st.text_input("Enter Brand for Car 1")
    model1 = st.text_input("Enter Model for Car 1")
    brand2 = st.text_input("Enter Brand for Car 2")
    model2 = st.text_input("Enter Model for Car 2")

    if brand1 and model1 and brand2 and model2:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Step 1: Fetch variants
            fetch_variants_query = """
            SELECT vehicle_id, brand, model, variant
            FROM Vehicle
            WHERE (LOWER(brand) = LOWER(%s) AND LOWER(model) = LOWER(%s))
            OR (LOWER(brand) = LOWER(%s) AND LOWER(model) = LOWER(%s))
            """
            cursor.execute(fetch_variants_query, (brand1, model1, brand2, model2))
            variant_rows = cursor.fetchall()

            car1_variants = [v for v in variant_rows if v['brand'] == brand1 and v['model'] == model1]
            car2_variants = [v for v in variant_rows if v['brand'] == brand2 and v['model'] == model2]

            st.subheader("✅ Select Variants to Compare")

            variant1 = st.selectbox("Select Variant for Car 1", [v["variant"] for v in car1_variants])
            variant2 = st.selectbox("Select Variant for Car 2", [v["variant"] for v in car2_variants])

            if st.button("🔍 Compare Selected Variants"):
                # Step 2: Fetch full data for selected variants
                compare_query = """
                SELECT
                    v.vehicle_id, v.brand, v.model, v.variant, v.type, v.image_link,
                    e.fuel, e.displacement, e.no_of_cylinders, e.bhp_value, e.bhp_rpm, e.torque_value, e.torque_rpm,
                    t.transmission, t.gearbox, t.drive_type,
                    p1.price AS chennai_price,
                    p2.price AS mumbai_price,
                    perf.mileage, perf.capacity,
                    d.boot_space, d.seating_capacity, d.wheel_base,
                    ch.front_brake, ch.rear_brake, ch.tyre_size, ch.tyre_type,
                    f.cruise_control, f.parking_sensors, f.keyLess_entry, f.engine_start_stop_button,
                    f.LED_headlamps, f.no_of_airbags, f.rear_camera, f.hill_assist
                FROM Vehicle v
                LEFT JOIN Engine e ON v.vehicle_id = e.vehicle_id
                LEFT JOIN Transmission t ON v.vehicle_id = t.vehicle_id
                LEFT JOIN Performance perf ON v.vehicle_id = perf.vehicle_id
                LEFT JOIN Dimensions d ON v.vehicle_id = d.vehicle_id
                LEFT JOIN Chassis ch ON v.vehicle_id = ch.vehicle_id
                LEFT JOIN Features f ON v.vehicle_id = f.vehicle_id
                LEFT JOIN Price p1 ON v.vehicle_id = p1.vehicle_id AND p1.city = 'Chennai'
                LEFT JOIN Price p2 ON v.vehicle_id = p2.vehicle_id AND p2.city = 'Mumbai'
                WHERE v.variant = %s OR v.variant = %s
                """

                cursor.execute(compare_query, (variant1, variant2))
                cars = cursor.fetchall()

                if cars and len(cars) == 2:
                    car1, car2 = cars[0], cars[1]

                    # Create DataFrame for display
                    comparison_data = {
                        "Feature": [
                            "Brand & Model", "Variant", "Fuel", "Transmission", "Drive Type",
                            "Displacement (cc)", "Mileage (km/l)", "Boot Space (L)", "Seating Capacity",
                            "BHP @ RPM", "Torque @ RPM", "Gearbox", "Tyres", "Brakes (Front/Rear)",
                            "Chennai Price (₹)", "Mumbai Price (₹)", "Airbags", "Cruise Control",
                            "Keyless Entry", "Rear Camera", "Hill Assist", "LED Headlamps",
                            "Parking Sensors", "Engine Start/Stop"
                        ],
                        f"{car1['brand']} {car1['model']} ({car1['variant']})": [
                            f"{car1['brand']} {car1['model']}", car1['variant'], car1['fuel'], car1['transmission'],
                            car1['drive_type'], car1['displacement'], car1['mileage'], car1['boot_space'],
                            car1['seating_capacity'], f"{car1['bhp_value']} @ {car1['bhp_rpm']} rpm",
                            f"{car1['torque_value']} @ {car1['torque_rpm']} rpm", car1['gearbox'],
                            f"{car1['tyre_size']} ({car1['tyre_type']})", f"{car1['front_brake']} / {car1['rear_brake']}",
                            f"₹{int(car1['chennai_price'] or 0):,}", f"₹{int(car1['mumbai_price'] or 0):,}",
                            car1['no_of_airbags'], '✅' if car1['cruise_control'] else '❌',
                            '✅' if car1['keyLess_entry'] else '❌', '✅' if car1['rear_camera'] else '❌',
                            '✅' if car1['hill_assist'] else '❌', '✅' if car1['LED_headlamps'] else '❌',
                            '✅' if car1['parking_sensors'] else '❌', '✅' if car1['engine_start_stop_button'] else '❌'
                        ],
                        f"{car2['brand']} {car2['model']} ({car2['variant']})": [
                            f"{car2['brand']} {car2['model']}", car2['variant'], car2['fuel'], car2['transmission'],
                            car2['drive_type'], car2['displacement'], car2['mileage'], car2['boot_space'],
                            car2['seating_capacity'], f"{car2['bhp_value']} @ {car2['bhp_rpm']} rpm",
                            f"{car2['torque_value']} @ {car2['torque_rpm']} rpm", car2['gearbox'],
                            f"{car2['tyre_size']} ({car2['tyre_type']})", f"{car2['front_brake']} / {car2['rear_brake']}",
                            f"₹{int(car2['chennai_price'] or 0):,}", f"₹{int(car2['mumbai_price'] or 0):,}",
                            car2['no_of_airbags'], '✅' if car2['cruise_control'] else '❌',
                            '✅' if car2['keyLess_entry'] else '❌', '✅' if car2['rear_camera'] else '❌',
                            '✅' if car2['hill_assist'] else '❌', '✅' if car2['LED_headlamps'] else '❌',
                            '✅' if car2['parking_sensors'] else '❌', '✅' if car2['engine_start_stop_button'] else '❌'
                        ]
                    }

                    df = pd.DataFrame(comparison_data)
                    st.dataframe(df, use_container_width=True)

                    # Optionally display car images
                    st.subheader("📸 Car Images")
                    cols = st.columns(2)
                    with cols[0]:
                        st.image(car1['image_link'], caption=f"{car1['brand']} {car1['model']} - {car1['variant']}", width=300)
                    with cols[1]:
                        st.image(car2['image_link'], caption=f"{car2['brand']} {car2['model']} - {car2['variant']}", width=300)
                else:
                    st.warning("Comparison data is incomplete or not available.")
                cursor.close()
                conn.close()

        except Exception as e:
            st.error(f"Error: {e}")
