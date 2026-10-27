#!/usr/bin/env python3
"""
Deterministic Synthetic Forensic Sample Asset Generator (`scripts/generate_samples.py`).

Generates legally redistributable, privacy-safe synthetic demonstration files for
CrimeVision AI across all four required modalities:
1. Staged Synthetic Forensic Images (`data/samples/images/`):
   - `synthetic_office_scene.jpg` (1280x720 staged office physical disturbance scene)
   - `synthetic_retail_store_scene.jpg` (1280x720 staged retail counter theft scene)
2. Synthetic Witness Audio Recordings + Sidecar Transcripts (`data/samples/audio/`):
   - `synthetic_witness_store_robbery.wav` (+ `.json` multilingual reference)
   - `synthetic_witness_office_burglary.wav` (+ `.json` multilingual reference)
3. Synthetic Surveillance CCTV Videos (`data/samples/videos/`):
   - `synthetic_store_cctv.mp4` (10s @ 10fps H.264 MP4, store theft sequence)
   - `synthetic_corridor_cctv.mp4` (8s @ 10fps H.264 MP4, routine normal activity)
4. Synthetic Tabular Benchmark Dataset (`data/samples/tabular/`):
   - `synthetic_forensic_benchmark.csv`

Uses ImageMagick (`convert`) and `ffmpeg` when installed on the host, with pure-Python
fallbacks so the script never crashes on minimal student setups.
"""

import csv
import json
import math
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "data" / "samples"
IMG_DIR = SAMPLES_DIR / "images"
AUD_DIR = SAMPLES_DIR / "audio"
VID_DIR = SAMPLES_DIR / "videos"
TAB_DIR = SAMPLES_DIR / "tabular"

for folder in (IMG_DIR, AUD_DIR, VID_DIR, TAB_DIR):
    folder.mkdir(parents=True, exist_ok=True)


def _has_cmd(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _find_system_ttf() -> str | None:
    """Locate an installed TrueType font if available; return None on fontless containers."""
    search_roots = [Path("/usr/share/fonts"), Path("/Library/Fonts"), Path("C:/Windows/Fonts")]
    for root in search_roots:
        if root.exists():
            for font_file in root.rglob("*.ttf"):
                return str(font_file)
    return None


def _text_args(ttf_path: str | None, pointsize: int, fill: str, items: list[tuple[int, int, str]]) -> list[str]:
    if not ttf_path:
        return []
    args = ["-font", ttf_path, "-fill", fill, "-stroke", "none", "-pointsize", str(pointsize)]
    for x, y, label in items:
        args.extend(["-draw", f"text {x},{y} '{label}'"])
    return args


def generate_images() -> list[str]:
    """Generate two 1280x720 staged synthetic forensic scene photographs."""
    created: list[str] = []
    office_jpg = IMG_DIR / "synthetic_office_scene.jpg"
    store_jpg = IMG_DIR / "synthetic_retail_store_scene.jpg"
    ttf = _find_system_ttf()

    if _has_cmd("convert"):
        # 1. Synthetic Staged Office Disturbance Scene (1280x720)
        office_cmd = [
            "convert",
            "-size", "1280x720",
            "xc:#1e2430",
            # Back wall & floor perspective
            "-fill", "#2a3242", "-draw", "polygon 0,0 1280,0 1120,250 160,250",
            "-fill", "#232a36", "-draw", "polygon 0,0 160,250 160,720 0,720",
            "-fill", "#232a36", "-draw", "polygon 1280,0 1120,250 1120,720 1280,720",
            "-fill", "#343d4e", "-draw", "polygon 160,250 1120,250 1280,720 0,720",
            # Floor grid tiles
            "-stroke", "#3e495d", "-strokewidth", "1",
            "-draw", "line 160,360 1120,360",
            "-draw", "line 100,480 1180,480",
            "-draw", "line 40,600 1240,600",
            "-draw", "line 640,250 640,720",
            "-draw", "line 400,250 260,720",
            "-draw", "line 880,250 1020,720",
            # Window frame on back wall
            "-fill", "#151c28", "-stroke", "#526079", "-strokewidth", "3",
            "-draw", "rectangle 420,45 860,185",
            "-draw", "line 640,45 640,185",
            # Office Desk (right-center)
            "-fill", "#5c4332", "-stroke", "#3c2a1e", "-strokewidth", "2",
            "-draw", "polygon 700,220 1080,220 1130,330 680,330",
            "-fill", "#463224",
            "-draw", "rectangle 700,330 725,430",
            "-draw", "rectangle 1085,330 1110,430",
            # Open Laptop on Desk
            "-fill", "#cbd5e1", "-stroke", "#475569", "-strokewidth", "2",
            "-draw", "polygon 810,200 950,200 940,265 820,265",
            "-fill", "#38bdf8",
            "-draw", "polygon 820,208 940,208 932,258 828,258",
            "-fill", "#94a3b8",
            "-draw", "polygon 820,265 940,265 965,295 805,295",
            # Overturned Office Chair (left)
            "-fill", "#1e293b", "-stroke", "#64748b", "-strokewidth", "3",
            "-draw", "roundrectangle 185,260 365,380 12,12",
            "-draw", "line 275,380 230,445",
            "-draw", "line 275,380 330,440",
            # Forensic Mannequin Silhouette on Floor (center)
            "-fill", "#475569", "-stroke", "#cbd5e1", "-strokewidth", "2",
            "-draw", "circle 445,455 445,488",
            "-draw", "roundrectangle 485,430 735,515 24,24",
            "-draw", "roundrectangle 735,438 860,468 10,10",
            "-draw", "roundrectangle 735,482 855,512 10,10",
            # Metallic Knife Prop on Floor (bottom-left of center)
            "-fill", "#e2e8f0", "-stroke", "#94a3b8", "-strokewidth", "1",
            "-draw", "polygon 280,520 355,505 345,525",
            "-fill", "#111827",
            "-draw", "rectangle 355,503 392,522",
            # Yellow Forensic Evidence Markers (#1, #2, #3) with vector pip ticks
            "-fill", "#facc15", "-stroke", "#854d0e", "-strokewidth", "2",
            "-draw", "polygon 255,555 280,505 305,555",
            "-draw", "polygon 395,545 420,495 445,545",
            "-draw", "polygon 765,315 790,265 815,315",
            "-fill", "#0f172a", "-stroke", "none",
            "-draw", "rectangle 278,528 282,547",
            "-draw", "rectangle 414,520 418,539",
            "-draw", "rectangle 422,520 426,539",
            "-draw", "rectangle 782,290 785,309",
            "-draw", "rectangle 789,290 792,309",
            "-draw", "rectangle 796,290 799,309",
            # Forensic Camera Header Bar + REC indicator
            "-fill", "#0f172acc", "-draw", "rectangle 20,18 610,60",
            "-fill", "#ef4444", "-draw", "circle 42,39 42,46",
        ]
        office_cmd.extend(_text_args(ttf, 18, "#e2e8f0", [(62, 45, "SYNTHETIC FORENSIC SCENE // CASE-01 OFFICE")]))
        office_cmd.append(str(office_jpg))
        subprocess.run(office_cmd, check=True)

        # 2. Synthetic Staged Retail Store Counter Scene (1280x720)
        store_cmd = [
            "convert",
            "-size", "1280x720",
            "xc:#1b222c",
            # Walls & retail floor
            "-fill", "#273140", "-draw", "polygon 0,0 1280,0 1140,240 140,240",
            "-fill", "#394658", "-draw", "polygon 140,240 1140,240 1280,720 0,720",
            # Glass Jewelry / Retail Display Counter (right-center)
            "-fill", "#1e3a5f", "-stroke", "#7dd3fc", "-strokewidth", "3",
            "-draw", "polygon 590,275 1070,275 1110,565 565,565",
            "-fill", "#38bdf844",
            "-draw", "polygon 605,290 1055,290 1085,420 585,420",
            # Standing Figure Silhouette by Counter (left-center)
            "-fill", "#334155", "-stroke", "#cbd5e1", "-strokewidth", "2",
            "-draw", "circle 385,235 385,272",
            "-draw", "roundrectangle 335,278 440,465 20,20",
            "-draw", "rectangle 345,465 382,590",
            "-draw", "rectangle 398,465 435,590",
            # Handbag carried near waist
            "-fill", "#0f172a", "-stroke", "#94a3b8", "-strokewidth", "2",
            "-draw", "roundrectangle 442,380 545,485 10,10",
            "-draw", "arc 462,345 525,405 180,360",
            # Dropped Necklace Case on Floor
            "-fill", "#f59e0b", "-stroke", "#fef3c7", "-strokewidth", "2",
            "-draw", "circle 695,525 695,552",
            # Yellow Forensic Markers
            "-fill", "#facc15", "-stroke", "#854d0e", "-strokewidth", "2",
            "-draw", "polygon 635,560 660,510 685,560",
            "-draw", "polygon 510,535 535,485 560,535",
            "-fill", "#0f172a", "-stroke", "none",
            "-draw", "rectangle 658,533 662,552",
            "-draw", "rectangle 531,508 535,527",
            "-draw", "rectangle 538,508 542,527",
            "-fill", "#0f172acc", "-draw", "rectangle 20,18 650,60",
            "-fill", "#38bdf8", "-draw", "circle 42,39 42,46",
        ]
        store_cmd.extend(_text_args(ttf, 18, "#e2e8f0", [(62, 45, "SYNTHETIC FORENSIC SCENE // CASE-02 RETAIL STORE")]))
        store_cmd.append(str(store_jpg))
        subprocess.run(store_cmd, check=True)
    else:
        # Pure-Python minimal valid PPM fallback
        for target in (office_jpg, store_jpg):
            target.write_bytes(
                b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xd9"
            )

    created.extend([str(office_jpg), str(store_jpg)])
    return created


def _write_synthetic_speech_cadence_wav(wav_path: Path, duration_sec: float = 16.0, sample_rate: int = 16000) -> None:
    """
    Create a valid 16kHz 16-bit mono PCM WAV file with modulated voice-band formants
    and natural syllabic pauses so audio waveform players, duration probes, and ASR
    pipelines process a clean, non-silent signal.
    """
    total_samples = int(duration_sec * sample_rate)
    frames = bytearray()
    for i in range(total_samples):
        t = i / float(sample_rate)
        # Syllabic envelope (~3.5 syllables/sec with breath pauses every 4s)
        breath = 0.0 if (t % 4.0) > 3.55 else 1.0
        syllable_env = max(0.0, math.sin(2.0 * math.pi * 3.4 * t)) * breath
        # Fundamental f0 (~145 Hz) + first two vocal formants (440 Hz, 1180 Hz)
        f0 = 142.0 + 18.0 * math.sin(2.0 * math.pi * 0.6 * t)
        val = (
            0.55 * math.sin(2.0 * math.pi * f0 * t)
            + 0.28 * math.sin(2.0 * math.pi * (f0 * 3.0) * t)
            + 0.14 * math.sin(2.0 * math.pi * 1120.0 * t)
        ) * syllable_env
        pcm = max(-32767, min(32767, int(val * 11000)))
        frames.extend(struct.pack("<h", pcm))

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))


def generate_audio() -> list[str]:
    """Generate synthetic witness statement WAV files and structured multilingual sidecars."""
    created: list[str] = []

    store_wav = AUD_DIR / "synthetic_witness_store_robbery.wav"
    _write_synthetic_speech_cadence_wav(store_wav, duration_sec=20.0)
    store_meta = {
        "case_label": "Synthetic Witness Statement — Retail Store Robbery",
        "transcript_en": (
            "I was standing across Maple Avenue at 8:14 p.m. when I saw two masked individuals "
            "force open the retail store entrance. Inside the store they grabbed items from the "
            "glass display case and stuffed them into a dark handbag. While running out toward "
            "the side parking lot, one person dropped a gold necklace case near the doorway "
            "before both fled in a dark sedan as the alarm sounded."
        ),
        "segments": [
            {
                "start_raw": 0.0,
                "end_raw": 5.5,
                "text": "I was standing across Maple Avenue at 8:14 p.m. when two masked individuals forced open the retail store entrance.",
            },
            {
                "start_raw": 5.5,
                "end_raw": 11.5,
                "text": "Inside the store they grabbed items from the glass display case and stuffed them into a dark handbag.",
            },
            {
                "start_raw": 11.5,
                "end_raw": 16.0,
                "text": "While running out toward the side parking lot, one person dropped a gold necklace case near the doorway.",
            },
            {
                "start_raw": 16.0,
                "end_raw": 20.0,
                "text": "Both individuals entered a dark sedan and fled right as the store alarm started ringing.",
            },
        ],
        "translations": {
            "english": (
                "I was standing across Maple Avenue at 8:14 p.m. when I saw two masked individuals "
                "force open the retail store entrance. Inside the store they grabbed items from the "
                "glass display case and stuffed them into a dark handbag. While running out toward "
                "the side parking lot, one person dropped a gold necklace case near the doorway "
                "before both fled in a dark sedan as the alarm sounded."
            ),
            "hindi": (
                "मैं रात 8:14 बजे मेपल एवेन्यू के सामने खड़ा था जब मैंने दो नकाबपोश व्यक्तियों को रिटेल स्टोर "
                "का दरवाजा जबरन खोलते देखा। स्टोर के अंदर उन्होंने कांच के डिस्प्ले केस से सामान उठाया और काले हैंडबैग "
                "में भर लिया। बगल की पार्किंग की ओर भागते समय एक व्यक्ति के हाथ से दरवाजे के पास सोने के हार का डिब्बा "
                "गिर गया और अलार्म बजते ही दोनों एक गहरे रंग की सेडान कार में फरार हो गए।"
            ),
            "telugu": (
                "రాత్రి 8:14 గంటలకు నేను మేపుల్ అవెన్యూ ఎదురుగా నిలబడి ఉన్నప్పుడు ఇద్దరు ముసుగు ధరించిన వ్యక్తులు "
                "రిటైల్ స్టోర్ ప్రవేశద్వారాన్ని బలవంతంగా తెరవడం చూశాను. స్టోర్ లోపల గాజు డిస్‌ప్లే కేస్ నుండి వస్తువులను తీసి "
                "నల్లటి హ్యాండ్‌బ్యాగ్‌లో నింపారు. పక్కనే ఉన్న పార్కింగ్ స్థలం వైపు పరిగెత్తుతుండగా ద్వారం వద్ద బంగారు నెక్లెస్ బాక్స్ "
                "పడిపోయింది మరియు అలారం మోగగానే ఇద్దరూ కారులో పారిపోయారు."
            ),
            "french": (
                "Je me tenais en face de Maple Avenue à 20h14 lorsque j'ai vu deux individus masqués "
                "forcer l'entrée du magasin de détail. À l'intérieur du magasin, ils ont saisi des articles "
                "dans la vitrine en verre et les ont mis dans un sac à main sombre. En courant vers le parking "
                "latéral, l'un d'eux a fait tomber un écrin de collier près de la porte avant de fuir en berline."
            ),
        },
    }
    store_wav.with_suffix(".json").write_text(json.dumps(store_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    office_wav = AUD_DIR / "synthetic_witness_office_burglary.wav"
    _write_synthetic_speech_cadence_wav(office_wav, duration_sec=16.0)
    office_meta = {
        "case_label": "Synthetic Witness Statement — Office Disturbance",
        "transcript_en": (
            "Around 9:30 p.m. on the third-floor office wing I heard a loud crash coming from suite 304. "
            "When security unlocked the office door, an overturned chair and an open laptop on the desk "
            "were visible, along with a metallic knife lying on the floor beside a fallen person."
        ),
        "segments": [
            {
                "start_raw": 0.0,
                "end_raw": 5.5,
                "text": "Around 9:30 p.m. on the third-floor office wing I heard a loud crash coming from suite 304.",
            },
            {
                "start_raw": 5.5,
                "end_raw": 11.0,
                "text": "When security unlocked the office door, an overturned chair and an open laptop on the desk were visible.",
            },
            {
                "start_raw": 11.0,
                "end_raw": 16.0,
                "text": "We also noticed a metallic knife lying on the floor beside an unresponsive person and called emergency services.",
            },
        ],
        "translations": {
            "english": (
                "Around 9:30 p.m. on the third-floor office wing I heard a loud crash coming from suite 304. "
                "When security unlocked the office door, an overturned chair and an open laptop on the desk "
                "were visible, along with a metallic knife lying on the floor beside a fallen person."
            ),
            "hindi": (
                "रात लगभग 9:30 बजे तीसरी मंजिल के ऑफिस विंग में मैंने सुइट 304 से तेज आवाज सुनी। "
                "जब सुरक्षाकर्मी ने ऑफिस का दरवाजा खोला, तो वहां उल्टी पड़ी कुर्सी और मेज पर खुला लैपटॉप दिखाई दिया, "
                "साथ ही फर्श पर गिरे व्यक्ति के पास एक धातु का चाकू पड़ा था।"
            ),
            "telugu": (
                "రాత్రి సుమారు 9:30 గంటలకు మూడవ అంతస్తు ఆఫీస్ విభాగంలోని సూట్ 304 నుండి పెద్ద శబ్దం వినిపించింది. "
                "సెక్యూరిటీ ఆఫీస్ తలుపు తెరిచినప్పుడు బోల్తా పడిన కుర్చీ, డెస్క్‌పై తెరిచి ఉన్న ల్యాప్‌టాప్ మరియు నేలపై పడి ఉన్న "
                "వ్యక్తి పక్కన ఒక కత్తి కనిపించాయి."
            ),
            "french": (
                "Vers 21h30, dans l'aile des bureaux du troisième étage, j'ai entendu un grand bruit provenant "
                "du bureau 304. Lorsque la sécurité a ouvert la porte du bureau, une chaise renversée et un "
                "ordinateur portable ouvert sur le bureau étaient visibles, ainsi qu'un couteau métallique au sol."
            ),
        },
    }
    office_wav.with_suffix(".json").write_text(json.dumps(office_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    created.extend([str(store_wav), str(office_wav)])
    return created


def generate_videos() -> list[str]:
    """Generate two H.264 MP4 synthetic CCTV clips using ImageMagick + FFmpeg."""
    created: list[str] = []
    store_mp4 = VID_DIR / "synthetic_store_cctv.mp4"
    corridor_mp4 = VID_DIR / "synthetic_corridor_cctv.mp4"
    ttf = _find_system_ttf()

    if not (_has_cmd("convert") and _has_cmd("ffmpeg")):
        return created

    # Clip 1: 10-second Retail Store Theft Sequence (10 fps -> 100 frames)
    with tempfile.TemporaryDirectory() as tmp_frames:
        tmp_dir = Path(tmp_frames)
        for frame_idx in range(100):
            t_sec = frame_idx / 10.0
            whole_sec = int(t_sec)
            prog_x = int(50 + (t_sec / 10.0) * 560)
            cmd = [
                "convert", "-size", "640x360", "xc:#18202c",
                "-fill", "#273244", "-draw", "rectangle 0,0 640,130",
                "-fill", "#364357", "-draw", "rectangle 0,130 640,360",
                # Retail display counter on right
                "-fill", "#1e3a5f", "-stroke", "#7dd3fc", "-strokewidth", "2",
                "-draw", "rectangle 350,155 575,285",
            ]
            # Moving person enters at t=2.0s, reaches counter at t=4.5s, grabs bag & exits rapidly t=6.5..9.0s
            if 2.0 <= t_sec <= 9.2:
                if t_sec < 4.5:
                    px = int(60 + (t_sec - 2.0) * 105)
                elif t_sec < 6.5:
                    px = 322
                else:
                    px = int(322 - (t_sec - 6.5) * 115)
                py = 140
                cmd.extend([
                    "-fill", "#cbd5e1", "-stroke", "#0f172a", "-strokewidth", "1",
                    "-draw", f"circle {px},{py} {px},{py+18}",
                    "-fill", "#475569",
                    "-draw", f"roundrectangle {px-22},{py+20} {px+22},{py+105} 8,8",
                ])
                if t_sec >= 5.0:
                    # Handbag carried away from counter
                    cmd.extend([
                        "-fill", "#f59e0b",
                        "-draw", f"rectangle {px+20},{py+52} {px+52},{py+86}",
                    ])

            status_txt = (
                "ROUTINE_IDLE" if t_sec < 2.0 else "SUBJECT_AT_COUNTER" if t_sec < 6.5 else "RAPID_EXIT_BAG_TAKEN"
            )
            dot_color = "#10b981" if t_sec < 2.0 else "#f59e0b" if t_sec < 6.5 else "#ef4444"
            cmd.extend([
                "-fill", "#0f172acc", "-stroke", "none",
                "-draw", "rectangle 10,8 630,38",
                "-fill", dot_color,
                "-draw", "circle 26,23 26,29",
                "-fill", "#334155",
                "-draw", "rectangle 48,31 612,35",
                "-fill", "#38bdf8",
                "-draw", f"rectangle 48,31 {prog_x},35",
            ])
            cmd.extend(
                _text_args(ttf, 13, "#e2e8f0", [(48, 25, f"CAM-04 RETAIL STORE // 00:{whole_sec:02d} // {status_txt}")])
            )
            cmd.append(str(tmp_dir / f"frame_{frame_idx:04d}.jpg"))
            subprocess.run(cmd, check=True)

        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-framerate", "10",
                "-i", str(tmp_dir / "frame_%04d.jpg"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(store_mp4),
            ],
            check=True,
        )
        created.append(str(store_mp4))

    # Clip 2: 8-second Routine Corridor Walkthrough (Normal Activity baseline)
    with tempfile.TemporaryDirectory() as tmp_frames2:
        tmp_dir2 = Path(tmp_frames2)
        for frame_idx in range(80):
            t_sec = frame_idx / 10.0
            whole_sec = int(t_sec)
            px = int(90 + t_sec * 58)
            prog_x = int(50 + (t_sec / 8.0) * 560)
            cmd = [
                "convert", "-size", "640x360", "xc:#1d2532",
                "-fill", "#2c3749", "-draw", "rectangle 0,0 640,140",
                "-fill", "#3c4a61", "-draw", "rectangle 0,140 640,360",
                "-fill", "#94a3b8", "-stroke", "#0f172a", "-strokewidth", "1",
                "-draw", f"circle {px},148 {px},164",
                "-fill", "#64748b",
                "-draw", f"roundrectangle {px-18},168 {px+18},250 7,7",
                "-fill", "#0f172acc", "-stroke", "none",
                "-draw", "rectangle 10,8 630,38",
                "-fill", "#10b981",
                "-draw", "circle 26,23 26,29",
                "-fill", "#334155",
                "-draw", "rectangle 48,31 612,35",
                "-fill", "#10b981",
                "-draw", f"rectangle 48,31 {prog_x},35",
            ]
            cmd.extend(
                _text_args(ttf, 13, "#e2e8f0", [(48, 25, f"CAM-01 OFFICE CORRIDOR // 00:{whole_sec:02d} // NORMAL_WALKING")])
            )
            cmd.append(str(tmp_dir2 / f"frame_{frame_idx:04d}.jpg"))
            subprocess.run(cmd, check=True)

        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-framerate", "10",
                "-i", str(tmp_dir2 / "frame_%04d.jpg"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(corridor_mp4),
            ],
            check=True,
        )
        created.append(str(corridor_mp4))

    return created


def generate_tabular_benchmark() -> str:
    """Create synthetic ground-truth benchmark CSV for quantitative pipeline evaluation."""
    csv_path = TAB_DIR / "synthetic_forensic_benchmark.csv"
    rows = [
        {
            "case_id": "BENCH-001",
            "vision_location": "retail store",
            "vision_objects": "Human|display case|handbag|necklace",
            "audio_location": "store",
            "audio_transcript": "Two masked individuals ran out of the retail store carrying a dark handbag and dropped a necklace.",
            "expected_consistency": "consistent",
            "video_weapons": 0,
            "video_caption_hint": "Individual grabs handbag from counter and runs toward exit",
            "expected_video_class": "SUSPICIOUS RAPID MOVEMENT",
            "chat_query": "What happened at 00:05?",
            "expected_time_sec": 5,
        },
        {
            "case_id": "BENCH-002",
            "vision_location": "office",
            "vision_objects": "Human|knife|laptop|chair|desk",
            "audio_location": "office",
            "audio_transcript": "Inside the office suite an open laptop was on the desk and a knife lay beside a fallen person.",
            "expected_consistency": "consistent",
            "video_weapons": 1,
            "video_caption_hint": "Individual holding knife near office desk",
            "expected_video_class": "POTENTIAL WEAPON / SAFETY ALERT",
            "chat_query": "Check activity at 12 seconds",
            "expected_time_sec": 12,
        },
        {
            "case_id": "BENCH-003",
            "vision_location": "office",
            "vision_objects": "laptop|desk",
            "audio_location": "parking lot",
            "audio_transcript": "Witness reported a loud argument in the outdoor parking lot near a sedan.",
            "expected_consistency": "conflict",
            "video_weapons": 0,
            "video_caption_hint": "Employee walking calmly down corridor",
            "expected_video_class": "NORMAL ACTIVITY",
            "chat_query": "Describe timestamp 01:04",
            "expected_time_sec": 64,
        },
        {
            "case_id": "BENCH-004",
            "vision_location": "parking lot",
            "vision_objects": "Human|handbag",
            "audio_location": "parking lot",
            "audio_transcript": "A person walked across the parking lot carrying a handbag toward the exit.",
            "expected_consistency": "consistent",
            "video_weapons": 0,
            "video_caption_hint": "Person walking calmly across lot",
            "expected_video_class": "NORMAL ACTIVITY",
            "chat_query": "What objects were detected?",
            "expected_time_sec": -1,
        },
        {
            "case_id": "BENCH-005",
            "vision_location": "warehouse",
            "vision_objects": "Human|box",
            "audio_location": "bedroom",
            "audio_transcript": "Noise was heard upstairs inside the residential bedroom.",
            "expected_consistency": "conflict",
            "video_weapons": 0,
            "video_caption_hint": "Subject forced entry through warehouse door",
            "expected_video_class": "SUSPICIOUS RAPID MOVEMENT",
            "chat_query": "Was anything recorded at 00:09?",
            "expected_time_sec": 9,
        },
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return str(csv_path)


def write_data_manifest() -> None:
    """Document synthetic provenance, licensing, and regeneration instructions."""
    manifest = SAMPLES_DIR / "DATA_SOURCES_AND_LICENSES.md"
    manifest.write_text(
        """# Sample Datasets, Synthetic Media & Licensing Manifest

All demonstration files in `data/samples/` are **100% synthetic, deterministically generated assets** created specifically for the **CrimeVision AI** academic capstone project via `scripts/generate_samples.py`.

## Ethical & Legal Compliance
- **Zero Real Individuals**: No photographs, voices, or CCTV recordings of real individuals are used. Human figures are geometric silhouettes.
- **License**: Released under CC0 / MIT-compatible academic demonstration terms for unrestricted GitHub redistribution and classroom grading.

## Inventory of Generated Assets

| Modality | File Path | Specification | Intended Pipeline Demonstration |
| :--- | :--- | :--- | :--- |
| Image | `data/samples/images/synthetic_office_scene.jpg` | 1280x720 RGB JPEG | Staged office disturbance with desk, laptop, overturned chair, floor silhouette, knife prop, and numbered evidence markers (#1–#3) + 3D room projection. |
| Image | `data/samples/images/synthetic_retail_store_scene.jpg` | 1280x720 RGB JPEG | Staged retail store counter with display case, standing silhouette, handbag, and dropped necklace prop. |
| Audio | `data/samples/audio/synthetic_witness_store_robbery.wav` | 20.0s, 16kHz 16-bit Mono WAV + `.json` | Witness statement describing Maple Avenue retail store robbery, corroborated with `synthetic_retail_store_scene.jpg`, with English/Hindi/Telugu/French translations. |
| Audio | `data/samples/audio/synthetic_witness_office_burglary.wav` | 16.0s, 16kHz 16-bit Mono WAV + `.json` | Witness statement describing Suite 304 office crash, corroborated with `synthetic_office_scene.jpg`. |
| Video | `data/samples/videos/synthetic_store_cctv.mp4` | 10.0s, 640x360 @ 10fps H.264 MP4 | Surveillance sequence showing idle store (00:00–00:01), subject approaching counter (00:02–00:04), taking bag & rapid exit (00:05–00:09). |
| Video | `data/samples/videos/synthetic_corridor_cctv.mp4` | 8.0s, 640x360 @ 10fps H.264 MP4 | Routine corridor walkthrough demonstrating `NORMAL ACTIVITY` baseline classification. |
| Tabular | `data/samples/tabular/synthetic_forensic_benchmark.csv` | 5 Ground-Truth Cases (CSV) | Evaluates cross-modal consistency/conflict scoring, video crime classification, and Regex timestamp chat lookup via `scripts/run_evaluation.py`. |

## Regenerating Samples Locally

```bash
python3 scripts/generate_samples.py
```
""",
        encoding="utf-8",
    )


def main() -> None:
    imgs = generate_images()
    auds = generate_audio()
    vids = generate_videos()
    csv_file = generate_tabular_benchmark()
    write_data_manifest()
    print(
        json.dumps(
            {
                "status": "ok",
                "images_generated": len(imgs),
                "audio_generated": len(auds),
                "videos_generated": len(vids),
                "benchmark_csv": csv_file,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
