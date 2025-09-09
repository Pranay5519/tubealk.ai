import streamlit as st
summary = {'title': 'How Large Language Models (LLMs) Power Chatbots: A Deep Dive',

 'overview': 'This video explains how large language models (LLMs) work, focusing on their architecture (transformers), training process (pre-training and reinforcement learning), and the massive computational resources required.  It also touches upon the probabilistic nature of their predictions and the challenges in understanding their decision-making.',
 'key_points': [{'content': 'Chatbots function by repeatedly predicting the next word in a conversation using a large language model (LLM).',
   'timestamp': 33.38,
   'importance': 'high'},
  {'content': 'LLMs are sophisticated mathematical functions that assign probabilities to all possible next words in a text sequence.',
   'timestamp': 37.02,
   'importance': 'high'},
  {'content': 'LLMs are trained on massive datasets of text from the internet, requiring immense computational power (over 100 million years of computation for the largest models).',
   'timestamp': 88.04,
   'importance': 'high'},
  {'content': "Training involves adjusting parameters (weights) to improve the model's ability to predict the next word in a given sequence using backpropagation.",
   'timestamp': 108.2,
   'importance': 'high'},
  {'content': "The 'large' in LLM refers to the hundreds of billions of parameters that are adjusted during training, not set manually.",
   'timestamp': 127.86,
   'importance': 'medium'},
  {'content': 'LLMs undergo pre-training on vast text datasets and then reinforcement learning with human feedback to refine their responses and make them more helpful and user-friendly.',
   'timestamp': 227.54,
   'importance': 'high'},
  {'content': 'The use of GPUs enables the parallelization of computations, crucial for training LLMs efficiently.',
   'timestamp': 254.78,
   'importance': 'medium'},
  {'content': "Transformers, a key architecture in LLMs, process text in parallel using 'attention' mechanisms to consider the context of all words simultaneously.",
   'timestamp': 276.817,
   'importance': 'high'},
  {'content': 'The final prediction of the LLM is a probability distribution over all possible next words.',
   'timestamp': 382.48,
   'importance': 'medium'},
  {'content': 'The specific behavior of LLMs is an emergent property of their parameters, making it difficult to understand their exact decision-making process.',
   'timestamp': 392.794,
   'importance': 'medium'}],
 'main_topics': ['Large Language Models (LLMs)',
  'Chatbot Functionality',
  'Training Process (Pre-training & Reinforcement Learning)',
  'Transformer Architecture',
  'Computational Requirements',
  'Probabilistic Nature of Predictions'],
 'duration_summary': 'The video provides a comprehensive explanation of LLMs and chatbots, covering various aspects in a well-paced manner.  The length is appropriate for the depth of the subject matter.',
 'total_segments': 115,
 'video_duration': 453.101}
embed_url = "https://www.youtube.com/embed/3_TN1i3MTEU"
import streamlit as st


embed_url = "https://www.youtube.com/embed/3_TN1i3MTEU"

# Initialize session state
if "generated" not in st.session_state:
    st.session_state.generated = False
if "play_index" not in st.session_state:
    st.session_state.play_index = None  # store which key point to play

# Generate summary button
if st.button("Generate Summary"):
    st.session_state.generated = True
    st.session_state.play_index = None  # reset when generating

# Display summary if generated
if st.session_state.generated:
    st.header("📹 VIDEO SUMMARY")
    st.markdown("---")
    st.subheader("Title")
    st.write(summary['title'])

    st.subheader("Duration")
    st.write(f"{summary.get('video_duration', 0)/60:.2f} mins")

    st.subheader("Total Segments")
    st.write(summary.get('total_segments', 0))

    st.subheader("📋 OVERVIEW")
    st.write(summary['overview'])

    st.subheader("🎯 KEY POINTS:")
    for i, point in enumerate(summary['key_points'], 1):
        st.markdown(f"**{i}. {point['content']}**")
        col1, col2 = st.columns([3,1])
        col1.write(f"Importance: {point['importance']}")

        if col2.button("⏰ Play", key=f"play_{i}"):
            st.session_state.play_index = i - 1  # store index

        # Placeholder for the video below the key point
        if st.session_state.play_index == i - 1:
            timestamp = int(float(point['timestamp']))
            timestamp_url = f"{embed_url}?start={timestamp}&autoplay=1"
            st.markdown(f"""
                <iframe width="800" height="450"
                src="{timestamp_url}"
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; 
                encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
                </iframe>
            """, unsafe_allow_html=True)

    st.subheader("📚 MAIN TOPICS:")
    for topic in summary['main_topics']:
        st.write(f"• {topic}")

    st.subheader("⏱️ PACING ANALYSIS:")
    st.write(summary['duration_summary'])
