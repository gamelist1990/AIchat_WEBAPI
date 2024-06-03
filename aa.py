#!/usr/bin/env python
# coding: utf-8


# ██████╗   ███████╗ ██╗    ██╗ ███████╗            ██████╗    ██████╗             ██████╗   ██████╗    ██████╗   ███████╗
# ██╔══██╗ ██╔════╝ ██║    ██║ ██╔════╝            ██╔══██╗ ██╔═══██╗         ██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔════╝
# ██║    ██║ █████╗     ██║    ██║ ███████╗            ██║    ██║ ██║      ██║         ██║           ██║      ██║ ██║    ██║ █████╗  
# ██║    ██║ ██╔══╝    ╚██╗  ██╔╝ ╚════██║           ██║    ██║ ██║      ██║         ██║           ██║      ██║ ██║    ██║ ██╔══╝  
# ██████╔╝ ███████╗  ╚████╔╝  ███████║            ██████╔╝╚██████╔╝         ╚██████╗ ╚██████╔╝  ██████╔╝ ███████╗
# ╚═════╝  ╚══════╝    ╚═══╝     ╚══════╝            ╚═════╝    ╚═════╝             ╚═════╝   ╚═════╝    ╚═════╝   ╚══════╝


# # Made With 💓 By - [Devs Do Code](https://www.youtube.com/channel/@devsdocode)
# 
# 
# For any questions or concerns, reach out to us via our social media handles. Our top choice for contact is [Telegram](https://t.me/devsdocode). You can also find us on other platforms listed above. We're here to help!
# 
# - **YouTube Channel**: [https://www.youtube.com/@DevsDoCode](https://www.youtube.com/@DevsDoCode)
# - **Telegram Group**: [https://t.me/devsdocode](https://t.me/devsdocode)
# - **Discord Server**: [https://discord.gg/ehwfVtsAts](https://discord.gg/ehwfVtsAts)
# - **Instagram**:
#   - **Personal**: https://www.instagram.com/sree.shades_/
#   - **Channel**: https://www.instagram.com/devsdocode_/
# 
# ---
# 
# 🚀 Dive into the world of coding with [Devs Do Code](https://www.youtube.com/channel/@devsdocode) - where passion meets programming! Make sure to hit that Subscribe button to stay tuned for exciting content! 😊✨
# 
# **Pro Tip:** For optimal performance and a seamless experience, we recommend using the default library versions demonstrated in this demo. Your coding journey just got even better! Happy coding! 🖥️💻
# 

# # Overview

# ### Imports

# Importing Required Modules
import requests


# ### Defining Required Payloads

# Define the API endpoint URL

url = "https://alkalimakersuite-pa.clients6.google.com/$rpc/google.internal.alkali.applications.makersuite.v1.MakerSuiteService/GenerateContent"
model = "models/gemini-1.5-pro-latest"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
origin_url = "https://aistudio.google.com"
content_type = "application/json+protobuf"

# Authorization Tokens. 
# Could be Found in the Cookie list of https://aistudio.google.com/ 
# or Check out the Response Headers of a request made in from gemini 1.5 Pro Model (Check the Network Tab in the Developers Console for more infromation)

Authorization = "SAPISIDHASH"
Cookie = "SID=g.a000kAg-Icsu3P33xfSs4ghhr9N4jGZ9y01FtMLrtyQ3S8dn0mPlU2oMn3E7WNBozsJIZ8GrhgACgYKARsSARQSFQHGX2MiHR3RdIAcwcz5Uao8sJRQgBoVAUF8yKrClMigLWB1_IKIa9d8DCYA0076; __Secure-1PSID=g.a000kAg-Icsu3P33xfSs4ghhr9N4jGZ9y01FtMLrtyQ3S8dn0mPlGxIZ7vt1GzfWxlkIHy_H3gACgYKAc0SARQSFQHGX2MiHgKmlnb5qgW3op6Jl3xsHxoVAUF8yKo0mW1TKrRH33iAUzNxpa_j0076; __Secure-3PSID=g.a000kAg-Icsu3P33xfSs4ghhr9N4jGZ9y01FtMLrtyQ3S8dn0mPl1h7CqP9kJ3-sAkew2n3qIwACgYKAecSARQSFQHGX2MiKwcWFZAZdLdHa14-nbLHcRoVAUF8yKp2NkiwNbhE9soQyF7-OElr0076; HSID=AJxFm3i7HI5BplayS; SSID=AinfvjYku-iOi-KHn; APISID=PoqEqqFVL6WKw9Vn/APosODZZXN3mf6MmO; SAPISID=j0sEMqmTyYV3XCSE/AbBFe-IvVH9cE3PwR; __Secure-1PAPISID=j0sEMqmTyYV3XCSE/AbBFe-IvVH9cE3PwR; __Secure-3PAPISID=j0sEMqmTyYV3XCSE/AbBFe-IvVH9cE3PwR; SEARCH_SAMESITE=CgQIoJsB; NID=514=bi7AJwTPM8jlob8kqAmIJ_NXvGdPAY0bG6kcsCUJaBScBJVxQqBxMFRkM-XSmJk5MINiOfvNva97igdNVqp6cLgSgs6f4cooVsbCayTffPwwPQdvWgF9-bi9TZ01IoelR0omfPMxEIGuAH2o2PL1693OuzLizBflbdqpfeI3BF5Ca-qDXfJY23J16Iyy9urIRSelyoxc0bCgIkAtfaEEY98hIUKZTcGojhL-YzRlsgWvHrCInhXSy-Jcj8jJQURHi2EKAnVWG-3Ro4OH-thlCZReJGntapPMJl4FdgyGluEpBLlcL7oPQX90awgJ8mCxyxLEg4MbeQNdJRB_pA; 1P_JAR=2024-06-03-04; AEC=AQTF6HxI0as859prGnjCZk7Ud0-IbLhEhWUjo8yORASVxz5yUdVBef9T4FM; __Secure-1PSIDTS=sidts-CjIB3EgAEjY5Wj2eh9t_9SQeV7AFNubyzNGkTZL6kFfEvwKYrAgSw-fVy3Q4q8r_tjIAfxAA; __Secure-3PSIDTS=sidts-CjIB3EgAEjY5Wj2eh9t_9SQeV7AFNubyzNGkTZL6kFfEvwKYrAgSw-fVy3Q4q8r_tjIAfxAA; SIDCC=AKEyXzXRZ5lL2XbLNbuTKfBE44elQZJgv7185a_SkfRFB-tdSsbaFyLBy98M-kl4xgc6xKaQYw; __Secure-1PSIDCC=AKEyXzUcjYzHsd1mFOVuvYGIVfjIPHUxqObHL19cLlB-7DY3Hvm-DEZRonjBfUiw-60YatKwdcM; __Secure-3PSIDCC=AKEyXzVUnpnRXnUfe-B3M-suvnk1xxq5jIxtoUwYl97YRRyo-9i6IrRQ8QMTSUQZJ-qBUFRMNgo"
X_Google_Api_Key = "AIzaSyDdP816MREB3SkjZO04QXbjsigfcI0GWOs"
User_id = "xsWlxZ3NAAbnRXcHx0VCqWbkNVn51287ADQBEArZ1LkzTlsmHayrSXyTmwNdwymPQdO61STJO3B8C8dZqna72987ve8f5xFzYy50Z1hFAgAAALVSAAAAK2gBB34AOXOjZcR10v5p9eKcy2nXY9mVZkvIABX1pe0OBZN5sYFbWRYpTzywkZcn2NHUQkeLxOLa"


# Other Tuning Parameters (Optional)

max_tokens = 8192
temperature = 2
top_p = 0.4

stop_words = None
safety_settings = None
system_prompt = None

# Formatted Other Params
other_params = [[[None, None, 7, 2], [None, None, 8, 2], [None, None, 9, 2], [None, None, 10, 2]], [stop_words, safety_settings, system_prompt, max_tokens, temperature, top_p, 32]] 


# ### Requesting Endpoint

# Requesting Endpoint

# Set up the request headers
headers = {
    "Content-Type": content_type,
    "Authorization": Authorization,
    "Cookie": Cookie,
    "Origin": origin_url,
    "User-Agent": user_agent,
    "X-Goog-Api-Key": X_Google_Api_Key
}

# Prepare the payload data
payload = [
    model,
    [[[[None, "write something about the beauty of india"]], "user"]],
    other_params[0],
    other_params[1],
    User_id]

# Make a POST request to the API endpoint with the payload data and headers
response = requests.post(url, json=payload, headers=headers)

# Handle the response
if response.status_code == 200:
    print(response.text)
else:
    # If there was an error, print the error message
    print("Error:", response.status_code, response.reason)


# # Final Punchline

# #### Functions

# Function to extract the response content

def extract_before_model(data_list):
    extracted_list = []  # Initialize an empty list to store extracted strings
    
    # Iterate through the nested lists to find strings before "model"
    for item in data_list:
        if isinstance(item, list):  # Check if the item is a list
            extracted_list.extend(extract_before_model(item))  # Recursively call the function to handle nested lists
        elif isinstance(item, str) and item.strip() == 'model':  # Check if the item is "model"
            break  # Stop iterating when "model" is found
        elif isinstance(item, str):  # Check if the item is a string
            extracted_list.append(item)  # Add the string to the list
    
    return extracted_list

# format the output

def formatter(json_response):
    content = ""
    for object_string in json_response[0]:
        extracted_content = extract_before_model(object_string)
        content = content + extracted_content[0]

    return content

# Main Function

def Gemini_1_5(query):

    # Set up the request headers
    headers = {
        "Content-Type": content_type,
        "Authorization": Authorization,
        "Cookie": Cookie,
        "Origin": origin_url,
        "User-Agent": user_agent,
        "X-Goog-Api-Key": X_Google_Api_Key
    }

    # Prepare the payload data
    payload = [
        model,
        [[[[None, query]], "user"]],
        other_params[0],
        other_params[1],
        User_id
        ]

    # Make a POST request to the API endpoint with the payload data and headers
    response = requests.post(url, json=payload, headers=headers)

    # Handle the response
    if response.status_code == 200:
        output = formatter(response.json())
        return output
    else:
        # If there was an error, print the error message
        print("Error:", response.status_code, response.reason)


# #### Calling the Function

# Testing and debugging

output = Gemini_1_5("Describe about the beauty of India")
print(output)
