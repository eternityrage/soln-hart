import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Minimalist-Inspired Outfits for Quiet Elegance",
        "Everyday Beauty Routine for a Refined Glow",
        "Finding Elegance in Little Things: A Calm Day",
        "Travel Diary: A Refined Escape Worth Saving",
        "How to Build a Minimalist Capsule Wardrobe",
        "Soft Glam Makeup for an Elegant Evening",
        "Photography Tips for Capturing Quiet Moments",
        "Wellness Rituals That Help Me Feel Centered",
        "Chic Airport Looks for Effortless Travel",
        "Personal Style Inspiration: Dressing with Ease",
        "Cozy Knitwear Looks for Gentle Days",
        "Quiet Luxury: My Favorite Elegant Fashion",
        "A Peaceful Morning Routine to Start Beautifully",
        "Travel Adventures: Exploring a New City in Style",
        "Live Elegantly: Small Habits for a Lovely Life",
    ]

    fallback_descriptions = [
        "Fashion is a quiet kind of self-expression. These minimalist-inspired looks are refined, elegant, and easy to wear every day. Save this for your next outfit plan! 🤍 #fashion #style #minimalist #outfitinspo #solenessahartley",
        "Beauty starts with how you treat yourself. A simple routine, a little light, and you glow from within. Like if you love a natural look! 💄 #beauty #skincare #glow #selfcare #solenessahartley",
        "The little things are where elegance lives - morning light, a clean space, a slow cup of tea. Notice them today. Double tap if you agree! 🌿 #lifestyle #slowliving #everydaybeauty #mindful #solenessahartley",
        "Travel feeds the soul. A new city, pretty streets, and outfits that match the mood - this escape was pure calm. Comment your dream destination! ✈️ #travel #traveldiary #adventure #style #solenessahartley",
        "A refined wardrobe makes getting dressed effortless. A few quality pieces, mixed with love, go everywhere. Share this with a style friend! 🤍 #fashion #capsulewardrobe #minimalist #elegance #solenessahartley",
        "Soft glam is my favorite kind of evening look - glowing skin, a pretty lip, and quiet confidence. Save this for date night! 🌙 #beauty #makeup #glam #eveninglook #solenessahartley",
        "You don't need a fancy camera to capture beautiful moments - just light and attention. Try these simple tips today. Like if you love photography! 📸 #photography #everydaymoments #inspiration #solenessahartley",
        "Wellness is beauty from the inside out. A walk, water, rest, and kind thoughts make all the difference. Drop a 🌿 if you're prioritizing you! #wellness #selfcare #lifestyle #beauty #solenessahartley",
        "Travel in style starts at the airport. Comfy yet chic pieces keep you polished from takeoff to arrival. Save this travel look! ✈️ #travelstyle #airportlook #ootd #fashion #solenessahartley",
        "Dress for ease, not just occasions. When your outfit makes you feel calm, the whole day feels lighter. Comment your favorite piece! 👗 #personalstyle #fashion #styleinspo #solenessahartley",
        "Cozy knitwear is a love language. Soft textures, neutral tones, gentle days - my kind of comfort. Double tap if you love knits! 🧶 #knitwear #cozy #fashion #minimalist #solenessahartley",
        "Quiet luxury is forever in my wardrobe. It's refined, calm, and effortlessly elegant. Like if you love minimalism! 🤍 #minimalist #fashion #style #beauty #solenessahartley",
        "A peaceful morning sets the tone for a beautiful day. Light, stretch, a little skincare, and intention. Follow Solenessa Hartley for daily fashion, beauty, and lifestyle inspiration! ☀️ #morningroutine #lifestyle #wellness #solenessahartley",
        "New city, new stories. I love exploring in style - pretty cafes, hidden corners, and outfits made for wandering. Share this with a travel buddy! 🗺️ #travel #explore #citybreak #style #solenessahartley",
        "Live elegantly - not perfectly. Small, lovely habits turn ordinary days into something special. Be elegantly you. 🤍 #lifestyle #liveelegantly #selflove #inspiration #solenessahartley",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "soft and elegant - make viewers want to embrace minimalist, refined style",
        "warm and personal - share real beautiful everyday moments",
        "calm and travel-loving - emphasise escapes, adventures, and discovery",
        "beauty-focused - celebrate skincare, makeup, and self-care",
        "calm and mindful - emphasise slow living and the little things",
        "photography-inspired - encourage capturing everyday beauty",
        "uplifting - remind viewers to live elegantly and be themselves",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Solenessa Hartley'. "
        f"A space dedicated to fashion, beauty, lifestyle, travel, and beautiful everyday moments. Solenessa shares refined looks, minimalist-inspired fashion, travel adventures, wellness, photography, and personal-style inspiration - live elegantly, be elegantly you. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this inspired your style! Comment your favorite look below! Share this with a friend who loves fashion! Follow Solenessa Hartley for daily fashion, beauty, and lifestyle inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #fashion #beauty #lifestyle #travel #style #minimalist #photography #wellness #solenessahartley. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["fashion", "beauty", "lifestyle", "travel", "style", "minimalist", "quietluxury", "photography", "wellness", "solenessahartley", "ootd", "skincare", "selfcare", "inspiration", "liveelegantly"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
