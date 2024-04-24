import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models

def generate():
  vertexai.init(project="geminipro1-5", location="us-central1")
  # gemini-1.5-pro-preview-0409
  # gemini-1.0-pro-vision-001
  model = GenerativeModel("gemini-1.5-pro-preview-0409")
  response = model.generate_content(
      [text2],
      generation_config=generation_config,
      safety_settings=safety_settings,
      stream=False,
  )
  print(response.text)
  return response.text

# Enable for Stream
#  for response in responses:
#    print(response.text, end="")

text1 = """List capitals of some countries in North America. Answer as a valid JSON dictionary with the country name as the key and the capital as the value."""
text2 = """
INSTRUCTIONS: Find the keyword from the text below. The keyword is one word immediately following "Keyword: ". Output the keyword in JSON format.

abacustron, abalish, acordify, adox, affluency, agglo, airade, alarynth, alligrater, anast, anglonic, aniplex, apter, arcicle, argle, asque, atrical, aubade, aulic, auricle, avoke, axtuple, babblefest, badunk, bajillion, balderdashery, balkanize, banshee, barnicle, beasty, beefalo, befriend, bellower, benificent, bibble, bibble-babble, bicentennial, bigwig, blabbermouth, blatherskite, blarney, blather, blatherskite, blether, blubber, bluster, bodacious, bodkin, bollocks, bombastic, bonkers, bonzer, booby, booger, boondoggle, boondoggle, boozy, borborygm, bore, bosh, botch, bottle, bounce, bounder, bowdlerize, brain fart, brainwave, brazen, brickbat, bristle, brobdingnagian, buckshot, buddy-buddy, buffle, bugger, bull, bulldoze, bully, bumptious, bumble, bumble, bumbling, bumblehead, bungler, bunker, burble, burn, burnish, buzzy, cackle, cackle, cakewalk, callithumpian, candy-ass, cantankerous, caput, carbuncle, carpetbagger, cattywampus, chawbacon, cheese it, chew the cud, chicken, chicken out, chicken-hearted, chimbley, chock-full, chum, chum, chuck, chuckle, chump, cinder, clanger, clattered, clattered, clattery, claxon, clod, clomp, clomper, clompety, clompity-clomp, clop, clopper, cloppety, cloppety-clop, clumsy, clod, clodhopper, clodpole, clomper, clompety-clomp, clumsily, clumsiness, clunk, clunker, clunkety, clunkety-clunk, collywobbles, comfily, comfy, comfy-cozy, comfy-cosy, comfy-cozy, abacustron, abalish, acordify, adox, affluency, agglo, airade, alarynth, alligrater, anast, anglonic, aniplex, apter, arcicle, argle, asque, atrical, aubade, aulic, auricle, avoke, axtuple, babblefest, badunk, bajillion, balderdashery, balkanize, banshee, barnicle, beasty, beefalo, befriend, bellower, benificent, bibble, bibble-babble, bicentennial, bigwig, blabbermouth, blatherskite, blarney, blather, blatherskite, blether, blubber, bluster, bodacious, bodkin, bollocks, bombastic, bonkers, bonzer, booby, booger, boondoggle, boondoggle, boozy, borborygm, bore, bosh, botch, bottle, bounce, bounder, bowdlerize, brain fart, brainwave, brazen, brickbat, bristle, brobdingnagian, buckshot, buddy-buddy, buffle, bugger, bull, bulldoze, bully, bumptious, bumble, bumble, bumbling, bumblehead, bungler, bunker, burble, burn, burnish, buzzy, cackle, cackle, cakewalk, callithumpian, candy-ass, cantankerous, caput, carbuncle, carpetbagger, cattywampus, Keyword: ironmountain, chawbacon, cheese it, chew the cud, chicken, chicken out, chicken-hearted, chimbley, chock-full, chum, chum, chuck, chuckle, chump, cinder, clanger, clattered, clattered, clattery, claxon, clod, clomp, clomper, clompety, clompity-clomp, clop, clopper, cloppety, cloppety-clop, clumsy, clod, clodhopper, clodpole, clomper, clompety-clomp, clumsily, clumsiness, clunk, clunker, clunkety, clunkety-clunk, collywobbles, comfily, comfy, comfy-cozy, comfy-cosy, comfy-cozy,abacustron, abalish, acordify, adox, affluency, agglo, airade, alarynth, alligrater, anast, anglonic, aniplex, apter, arcicle, argle, asque, atrical, aubade, aulic, auricle, avoke, axtuple, babblefest, badunk, bajillion, balderdashery, balkanize, banshee, barnicle, beasty, beefalo, befriend, bellower, benificent, bibble, bibble-babble, bicentennial, bigwig, blabbermouth, blatherskite, blarney, blather, blatherskite, blether, blubber, bluster, bodacious, bodkin, bollocks, bombastic, bonkers, bonzer, booby, booger, boondoggle, boondoggle, boozy, borborygm, bore, bosh, botch, bottle, bounce, bounder, bowdlerize, brain fart, brainwave, brazen, brickbat, bristle, brobdingnagian, buckshot, buddy-buddy, buffle, bugger, bull, bulldoze, bully, bumptious, bumble, bumble, bumbling, bumblehead, bungler, bunker, burble, burn, burnish, buzzy, cackle, cackle, cakewalk, callithumpian, candy-ass, cantankerous, caput, carbuncle, carpetbagger, cattywampus, chawbacon, cheese it, chew the cud, chicken, chicken out, chicken-hearted, chimbley, chock-full, chum, chum, chuck, chuckle, chump, cinder, clanger, clattered, clattered, clattery, claxon, clod, clomp, clomper, clompety, clompity-clomp, clop, clopper, cloppety, cloppety-clop,
"""


generation_config = {
    "max_output_tokens": 2048,
    "temperature": 1.0,
    "top_p": 0.4,
    "top_k": 32,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

# generate()

text_result = []
for _ in range(5):
  text_result.append(generate())



print(text_result)
