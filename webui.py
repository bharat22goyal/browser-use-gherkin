import pdb
import logging
import json
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
import os
import glob
import asyncio
import argparse
import os

logger = logging.getLogger(__name__)

import gradio as gr

from browser_use.agent.service import Agent
from playwright.async_api import async_playwright
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import (
    BrowserContextConfig,
    BrowserContextWindowSize,
)
from langchain_ollama import ChatOllama
from playwright.async_api import async_playwright
from src.utils.agent_state import AgentState

from src.utils import utils
from src.agent.custom_agent import CustomAgent
from src.browser.custom_browser import CustomBrowser
from src.agent.custom_prompts import CustomSystemPrompt, CustomAgentMessagePrompt
from src.browser.custom_context import BrowserContextConfig, CustomBrowserContext
from src.controller.custom_controller import CustomController
from gradio.themes import Citrus, Default, Glass, Monochrome, Ocean, Origin, Soft, Base
from src.utils.default_config_settings import default_config, load_config_from_file, save_config_to_file, save_current_config, update_ui_from_config
from src.utils.utils import update_model_dropdown, get_latest_files, capture_screenshot


# Global variables for persistence
_global_browser = None
_global_browser_context = None

# Create the global agent state instance
_global_agent_state = AgentState()

async def stop_agent():
    """Request the agent to stop and update UI with enhanced feedback"""
    global _global_agent_state, _global_browser_context, _global_browser

    try:
        # Request stop
        _global_agent_state.request_stop()

        # Update UI immediately
        message = "Stop requested - the agent will halt at the next safe point"
        logger.info(f"🛑 {message}")

        # Return UI updates
        return (
            message,                                        # errors_output
            gr.update(value="Stopping...", interactive=False),  # stop_button
            gr.update(interactive=False),                      # run_button
        )
    except Exception as e:
        error_msg = f"Error during stop: {str(e)}"
        logger.error(error_msg)
        return (
            error_msg,
            gr.update(value="Stop", interactive=True),
            gr.update(interactive=True)
        )

async def run_browser_agent(
        agent_type,
        llm_provider,
        llm_model_name,
        llm_temperature,
        llm_base_url,
        llm_api_key,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        enable_recording,
        task,
        add_infos,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    global _global_agent_state
    _global_agent_state.clear_stop()  # Clear any previous stop requests

    try:
        # Disable recording if the checkbox is unchecked
        if not enable_recording:
            save_recording_path = None

        # Ensure the recording directory exists if recording is enabled
        if save_recording_path:
            os.makedirs(save_recording_path, exist_ok=True)

        # Get the list of existing videos before the agent runs
        existing_videos = set()
        if save_recording_path:
            existing_videos = set(
                glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4"))
                + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))
            )

        # Run the agent
        llm = utils.get_llm_model(
            provider=llm_provider,
            model_name=llm_model_name,
            temperature=llm_temperature,
            base_url=llm_base_url,
            api_key=llm_api_key,
        )
        if agent_type == "org":
            final_result, errors, model_actions, model_thoughts, trace_file, history_file = await run_org_agent(
                llm=llm,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                task=task,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method
            )
        elif agent_type == "custom":
            final_result, errors, model_actions, model_thoughts, trace_file, history_file = await run_custom_agent(
                llm=llm,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                task=task,
                add_infos=add_infos,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method
            )
        else:
            raise ValueError(f"Invalid agent type: {agent_type}")

        # Get the list of videos after the agent runs (if recording is enabled)
        latest_video = None
        if save_recording_path:
            new_videos = set(
                glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4"))
                + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))
            )
            if new_videos - existing_videos:
                latest_video = list(new_videos - existing_videos)[0]  # Get the first new video

        return (
            final_result,
            errors,
            model_actions,
            model_thoughts,
            latest_video,
            trace_file,
            history_file,
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        )

    except gr.Error:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return (
            '',                                         # final_result
            errors,                                     # errors
            '',                                         # model_actions
            '',                                         # model_thoughts
            None,                                       # latest_video
            None,                                       # history_file
            None,                                       # trace_file
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        )


async def run_org_agent(
        llm,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        task,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state
        
        # Clear any previous stop request
        _global_agent_state.clear_stop()

        extra_chromium_args = [f"--window-size={window_w},{window_h}"]
        if use_own_browser:
            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
            chrome_user_data = os.getenv("CHROME_USER_DATA", None)
            if chrome_user_data:
                extra_chromium_args += [f"--user-data-dir={chrome_user_data}"]
        else:
            chrome_path = None
            
        if _global_browser is None:
            _global_browser = Browser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    chrome_instance_path=chrome_path,
                    extra_chromium_args=extra_chromium_args,
                )
            )

        if _global_browser_context is None:
            _global_browser_context = await _global_browser.new_context(
                config=BrowserContextConfig(
                    trace_path=save_trace_path if save_trace_path else None,
                    save_recording_path=save_recording_path if save_recording_path else None,
                    no_viewport=False,
                    browser_window_size=BrowserContextWindowSize(
                        width=window_w, height=window_h
                    ),
                )
            )
            
        agent = Agent(
            task=task,
            llm=llm,
            use_vision=use_vision,
            browser=_global_browser,
            browser_context=_global_browser_context,
            max_actions_per_step=max_actions_per_step,
            tool_calling_method=tool_calling_method
        )
        history = await agent.run(max_steps=max_steps)

        history_file = os.path.join(save_agent_history_path, f"{agent.agent_id}.json")
        agent.save_history(history_file)

        final_result = history.final_result()
        errors = history.errors()
        model_actions = history.model_actions()
        model_thoughts = history.model_thoughts()

        trace_file = get_latest_files(save_trace_path)

        return final_result, errors, model_actions, model_thoughts, trace_file.get('.zip'), history_file
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return '', errors, '', '', None, None
    finally:
        # Handle cleanup based on persistence configuration
        if not keep_browser_open:
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None

            if _global_browser:
                await _global_browser.close()
                _global_browser = None

async def run_custom_agent(
        llm,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        task,
        add_infos,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state

        # Clear any previous stop request
        _global_agent_state.clear_stop()

        extra_chromium_args = [f"--window-size={window_w},{window_h}"]
        if use_own_browser:
            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
            chrome_user_data = os.getenv("CHROME_USER_DATA", None)
            if chrome_user_data:
                extra_chromium_args += [f"--user-data-dir={chrome_user_data}"]
        else:
            chrome_path = None

        controller = CustomController()

        # Initialize global browser if needed
        if _global_browser is None:
            _global_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    chrome_instance_path=chrome_path,
                    extra_chromium_args=extra_chromium_args,
                )
            )

        if _global_browser_context is None:
            _global_browser_context = await _global_browser.new_context(
                config=BrowserContextConfig(
                    trace_path=save_trace_path if save_trace_path else None,
                    save_recording_path=save_recording_path if save_recording_path else None,
                    no_viewport=False,
                    browser_window_size=BrowserContextWindowSize(
                        width=window_w, height=window_h
                    ),
                )
            )
            
        # Create and run agent
        agent = CustomAgent(
            task=task,
            add_infos=add_infos,
            use_vision=use_vision,
            llm=llm,
            browser=_global_browser,
            browser_context=_global_browser_context,
            controller=controller,
            system_prompt_class=CustomSystemPrompt,
            agent_prompt_class=CustomAgentMessagePrompt,
            max_actions_per_step=max_actions_per_step,
            agent_state=_global_agent_state,
            tool_calling_method=tool_calling_method
        )
        history = await agent.run(max_steps=max_steps)

        history_file = os.path.join(save_agent_history_path, f"{agent.agent_id}.json")
        agent.save_history(history_file)

        final_result = history.final_result()
        errors = history.errors()
        model_actions = history.model_actions()
        model_thoughts = history.model_thoughts()

        trace_file = get_latest_files(save_trace_path)        

        return final_result, errors, model_actions, model_thoughts, trace_file.get('.zip'), history_file
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return '', errors, '', '', None, None
    finally:
        # Handle cleanup based on persistence configuration
        if not keep_browser_open:
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None

            if _global_browser:
                await _global_browser.close()
                _global_browser = None

async def run_with_stream(
    agent_type,
    llm_provider,
    llm_model_name,
    llm_temperature,
    llm_base_url,
    llm_api_key,
    use_own_browser,
    keep_browser_open,
    headless,
    disable_security,
    window_w,
    window_h,
    save_recording_path,
    save_agent_history_path,
    save_trace_path,
    enable_recording,
    task,
    add_infos,
    max_steps,
    use_vision,
    max_actions_per_step,
    tool_calling_method
):
    global _global_agent_state
    stream_vw = 80
    stream_vh = int(80 * window_h // window_w)
    if not headless:
        result = await run_browser_agent(
            agent_type=agent_type,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            llm_temperature=llm_temperature,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            use_own_browser=use_own_browser,
            keep_browser_open=keep_browser_open,
            headless=headless,
            disable_security=disable_security,
            window_w=window_w,
            window_h=window_h,
            save_recording_path=save_recording_path,
            save_agent_history_path=save_agent_history_path,
            save_trace_path=save_trace_path,
            enable_recording=enable_recording,
            task=task,
            add_infos=add_infos,
            max_steps=max_steps,
            use_vision=use_vision,
            max_actions_per_step=max_actions_per_step,
            tool_calling_method=tool_calling_method
        )
        # Add HTML content at the start of the result array
        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Using browser...</h1>"
        yield [html_content] + list(result)
    else:
        try:
            _global_agent_state.clear_stop()
            # Run the browser agent in the background
            agent_task = asyncio.create_task(
                run_browser_agent(
                    agent_type=agent_type,
                    llm_provider=llm_provider,
                    llm_model_name=llm_model_name,
                    llm_temperature=llm_temperature,
                    llm_base_url=llm_base_url,
                    llm_api_key=llm_api_key,
                    use_own_browser=use_own_browser,
                    keep_browser_open=keep_browser_open,
                    headless=headless,
                    disable_security=disable_security,
                    window_w=window_w,
                    window_h=window_h,
                    save_recording_path=save_recording_path,
                    save_agent_history_path=save_agent_history_path,
                    save_trace_path=save_trace_path,
                    enable_recording=enable_recording,
                    task=task,
                    add_infos=add_infos,
                    max_steps=max_steps,
                    use_vision=use_vision,
                    max_actions_per_step=max_actions_per_step,
                    tool_calling_method=tool_calling_method
                )
            )

            # Initialize values for streaming
            html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Using browser...</h1>"
            final_result = errors = model_actions = model_thoughts = ""
            latest_videos = trace = history_file = None


            # Periodically update the stream while the agent task is running
            while not agent_task.done():
                try:
                    encoded_screenshot = await capture_screenshot(_global_browser_context)
                    if encoded_screenshot is not None:
                        html_content = f'<img src="data:image/jpeg;base64,{encoded_screenshot}" style="width:{stream_vw}vw; height:{stream_vh}vh ; border:1px solid #ccc;">'
                    else:
                        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>"
                except Exception as e:
                    html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>"

                if _global_agent_state and _global_agent_state.is_stop_requested():
                    yield [
                        html_content,
                        final_result,
                        errors,
                        model_actions,
                        model_thoughts,
                        latest_videos,
                        trace,
                        history_file,
                        gr.update(value="Stopping...", interactive=False),  # stop_button
                        gr.update(interactive=False),  # run_button
                    ]
                    break
                else:
                    yield [
                        html_content,
                        final_result,
                        errors,
                        model_actions,
                        model_thoughts,
                        latest_videos,
                        trace,
                        history_file,
                        gr.update(value="Stop", interactive=True),  # Re-enable stop button
                        gr.update(interactive=True)  # Re-enable run button
                    ]
                await asyncio.sleep(0.05)

            # Once the agent task completes, get the results
            try:
                result = await agent_task
                final_result, errors, model_actions, model_thoughts, latest_videos, trace, history_file, stop_button, run_button = result
            except gr.Error:
                final_result = ""
                model_actions = ""
                model_thoughts = ""
                latest_videos = trace = history_file = None

            except Exception as e:
                errors = f"Agent error: {str(e)}"

            yield [
                html_content,
                final_result,
                errors,
                model_actions,
                model_thoughts,
                latest_videos,
                trace,
                history_file,
                stop_button,
                run_button
            ]

        except Exception as e:
            import traceback
            yield [
                f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>",
                "",
                f"Error: {str(e)}\n{traceback.format_exc()}",
                "",
                "",
                None,
                None,
                None,
                gr.update(value="Stop", interactive=True),  # Re-enable stop button
                gr.update(interactive=True)    # Re-enable run button
            ]

# Define the theme map globally
theme_map = {
    "Default": Default(),
    "Soft": Soft(),
    "Monochrome": Monochrome(),
    "Glass": Glass(),
    "Origin": Origin(),
    "Citrus": Citrus(),
    "Ocean": Ocean(),
    "Base": Base()
}

async def close_global_browser():
    global _global_browser, _global_browser_context

    if _global_browser_context:
        await _global_browser_context.close()
        _global_browser_context = None

    if _global_browser:
        await _global_browser.close()
        _global_browser = None

def create_ui(config, theme_name="Ocean"):
    css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
        padding-top: 20px !important;
    }
    .header-text {
        text-align: center;
        margin-bottom: 30px;
    }
    .theme-section {
        margin-bottom: 20px;
        padding: 15px;
        border-radius: 10px;
    }
    """

    with gr.Blocks(
            title="Browser Use WebUI", theme=theme_map[theme_name], css=css
    ) as demo:
        with gr.Row():
            gr.Markdown(
                """
                # 🌐 Browser Use WebUI
                ### Control your browser with AI assistance
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("🧪 Gherkin Tests", id=1):
                with gr.Group():
                    gr.Markdown("### Gherkin Test Manager")
                    
                    with gr.Row():
                        # Test file management
                        feature_file_list = gr.Dropdown(
                            label="Available Feature Files",
                            choices=glob.glob("features/**/*.feature", recursive=True),
                            value=None,
                            info="Select a feature file to run",
                            allow_custom_value=False
                        )
                        refresh_features_button = gr.Button("🔄 Refresh", scale=0.2)
                    
                    with gr.Row():
                        # Test file viewer
                        feature_file_viewer = gr.TextArea(
                            label="Feature Content",
                            interactive=False,
                            lines=15
                        )
                    
                    with gr.Row():
                        # Add logging options
                        test_log_level = gr.Dropdown(
                            label="Logging Level",
                            choices=["INFO", "DEBUG", "WARNING", "ERROR"],
                            value="INFO",
                            info="Select logging detail level"
                        )
                        enable_complete_logging = gr.Checkbox(
                            label="Enable Complete Logging",
                            value=True,
                            info="Save complete test logs to file"
                        )
                        log_file_path = gr.Textbox(
                            label="Log File Path",
                            placeholder="./test-reports/test.log",
                            value="./test-reports/test.log",
                            info="Path to save complete test logs",
                            interactive=True
                        )
                        enable_html_report = gr.Checkbox(
                            label="Generate HTML Report",
                            value=True,
                            info="Generate detailed HTML test report"
                        )
                        html_report_path = gr.Textbox(
                            label="HTML Report Path",
                            placeholder="./test-reports/report.html",
                            value="./test-reports/report.html",
                            info="Path to save HTML report",
                            interactive=True
                        )

                    with gr.Row():
                        run_test_button = gr.Button("▶️ Run Selected Test", variant="primary")
                        run_all_tests_button = gr.Button("▶️ Run All Tests", variant="primary")
                        clear_results_button = gr.Button("🗑️ Clear Results")
                    
                    test_results = gr.Dataframe(
                        headers=["Feature", "Scenario", "Status", "Duration", "Error"],
                        label="Test Results",
                        interactive=False
                    )
                    
                    test_output = gr.Markdown(
                        label="Test Output",
                        value="",
                        show_label=True
                    )

                    def load_feature_content(feature_path):
                        if not feature_path:
                            return ""
                        try:
                            with open(feature_path, 'r') as f:
                                return f.read()
                        except Exception as e:
                            return f"Error loading feature file: {str(e)}"

                    async def run_selected_test(feature_path, log_level, enable_complete_logging, log_file_path, enable_html_report, html_report_path):
                        if not feature_path:
                            return [], "Please select a feature file to run"
                        return await run_gherkin_tests([feature_path], log_level, enable_complete_logging, log_file_path, enable_html_report, html_report_path)

                    async def run_all_gherkin_tests(log_level, enable_complete_logging, log_file_path, enable_html_report, html_report_path):
                        feature_files = glob.glob("features/**/*.feature", recursive=True)
                        return await run_gherkin_tests(feature_files, log_level, enable_complete_logging, log_file_path, enable_html_report, html_report_path)

                    async def run_gherkin_tests(feature_files, log_level, enable_complete_logging, log_file_path, enable_html_report, html_report_path):
                        try:
                            import json
                            import asyncio
                            from behave.__main__ import run_behave
                            from behave.configuration import Configuration
                            import logging
                            from datetime import datetime
                            import sys

                            # Create results directory if it doesn't exist
                            os.makedirs("test-reports", exist_ok=True)

                            # Configure logging
                            log_level_map = {
                                "DEBUG": logging.DEBUG,
                                "INFO": logging.INFO,
                                "WARNING": logging.WARNING,
                                "ERROR": logging.ERROR
                            }

                            # Reset root logger
                            root = logging.getLogger()
                            for handler in root.handlers[:]:
                                root.removeHandler(handler)

                            if enable_complete_logging and log_file_path:
                                # Create log directory
                                log_dir = os.path.dirname(log_file_path)
                                if log_dir:
                                    os.makedirs(log_dir, exist_ok=True)

                                # Add timestamp to log filename
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                base, ext = os.path.splitext(log_file_path)
                                timestamped_log_path = f"{base}_{timestamp}{ext}"

                                # Configure logging
                                file_handler = logging.FileHandler(timestamped_log_path, mode='w', encoding='utf-8')
                                file_handler.setLevel(log_level_map.get(log_level, logging.INFO))
                                file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                                file_handler.setFormatter(file_formatter)
                                
                                console_handler = logging.StreamHandler(sys.stdout)
                                console_handler.setLevel(log_level_map.get(log_level, logging.INFO))
                                console_formatter = logging.Formatter('%(levelname)s - %(message)s')
                                console_handler.setFormatter(console_formatter)
                                
                                root.setLevel(log_level_map.get(log_level, logging.INFO))
                                root.addHandler(file_handler)
                                root.addHandler(console_handler)
                                
                                logging.info(f"Log file created at: {timestamped_log_path}")

                            # Set up behave configuration
                            args = [
                                '--format=pretty',
                                f'--logging-level={log_level.lower()}',
                                '--define',
                                f'logging.level={log_level.lower()}'
                            ]

                            if enable_html_report and html_report_path:
                                # Create report directory
                                report_dir = os.path.dirname(html_report_path)
                                if report_dir:
                                    os.makedirs(report_dir, exist_ok=True)

                                # Add timestamp to report filename
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                base, ext = os.path.splitext(html_report_path)
                                timestamped_report_path = f"{base}_{timestamp}{ext}"

                                args.extend([
                                    '--format=behave_html_formatter:HTMLFormatter',
                                    f'--outfile={timestamped_report_path}'
                                ])

                            # Add feature files to run
                            args.extend(feature_files)

                            # Run behave with configuration
                            config = Configuration(args)
                            run_behave(config)

                            # Process results
                            results = []
                            output_lines = []

                            output_lines.append("### Test Execution Summary\n")
                            if enable_complete_logging:
                                output_lines.append(f"Complete logs saved to: {timestamped_log_path}\n")
                            if enable_html_report:
                                output_lines.append(f"HTML report generated at: {timestamped_report_path}\n")

                            # Add CSS to HTML report if it was generated
                            if enable_html_report and os.path.exists(timestamped_report_path):
                                with open(timestamped_report_path, 'r') as f:
                                    content = f.read()
                                
                                css = '''
                                <style>
                                    body { font-family: Arial, sans-serif; margin: 20px; }
                                    .feature { margin-bottom: 30px; }
                                    .scenario { margin: 20px 0; padding: 10px; background: #f5f5f5; }
                                    .passed { color: green; }
                                    .failed { color: red; }
                                    .skipped { color: orange; }
                                    .step { margin: 5px 0; }
                                    .description { font-style: italic; color: #666; }
                                </style>
                                '''
                                
                                content = content.replace('</head>', f'{css}</head>')
                                
                                with open(timestamped_report_path, 'w') as f:
                                    f.write(content)

                            return results, "\n".join(output_lines)

                        except Exception as e:
                            error_msg = f"Test execution failed: {str(e)}"
                            logging.error(error_msg)
                            return [], error_msg

                    def clear_test_results():
                        return None, ""

                    # Connect event handlers
                    refresh_features_button.click(
                        fn=lambda: gr.update(choices=glob.glob("features/**/*.feature", recursive=True)),
                        inputs=[],
                        outputs=[feature_file_list]
                    )

                    feature_file_list.change(
                        fn=load_feature_content,
                        inputs=[feature_file_list],
                        outputs=[feature_file_viewer]
                    )

                    run_test_button.click(
                        fn=run_selected_test,
                        inputs=[
                            feature_file_list,
                            test_log_level,
                            enable_complete_logging,
                            log_file_path,
                            enable_html_report,
                            html_report_path
                        ],
                        outputs=[test_results, test_output]
                    )

                    run_all_tests_button.click(
                        fn=run_all_gherkin_tests,
                        inputs=[
                            test_log_level,
                            enable_complete_logging,
                            log_file_path,
                            enable_html_report,
                            html_report_path
                        ],
                        outputs=[test_results, test_output]
                    )

                    clear_results_button.click(
                        fn=clear_test_results,
                        inputs=[],
                        outputs=[test_results, test_output]
                    )

                    enable_complete_logging.change(
                        lambda enabled: gr.update(interactive=enabled),
                        inputs=[enable_complete_logging],
                        outputs=[log_file_path]
                    )

                    enable_html_report.change(
                        lambda enabled: gr.update(interactive=enabled),
                        inputs=[enable_html_report],
                        outputs=[html_report_path]
                    )

            with gr.TabItem("🔍 Exploratory Testing", id=2):
                with gr.Group():
                    gr.Markdown("### Interactive Browser Testing")
                    
                    with gr.Row():
                        test_name = gr.Textbox(
                            label="Test Name",
                            placeholder="e.g., Search Functionality Test",
                            info="Give your test a descriptive name"
                        )
                        test_category = gr.Dropdown(
                            label="Test Category",
                            choices=["Navigation", "Search", "Form Interaction", "Visual Verification", "Other"],
                            value="Navigation",
                            info="Categorize your test"
                        )
                    
                    with gr.Row():
                        starting_url = gr.Textbox(
                            label="Starting URL",
                            placeholder="e.g., https://www.google.com",
                            info="The URL where the test will begin",
                            value="https://www.google.com"
                        )
                        test_task = gr.TextArea(
                            label="Test Task",
                            placeholder="Enter the task for the agent...",
                            info="Describe what the agent should do",
                            lines=2
                        )

                    with gr.Row():
                        # Add logging options
                        test_log_level = gr.Dropdown(
                            label="Logging Level",
                            choices=["INFO", "DEBUG", "WARNING", "ERROR"],
                            value="INFO",
                            info="Select logging detail level"
                        )
                        enable_test_logging = gr.Checkbox(
                            label="Save Test Results",
                            value=True,
                            info="Save test results and logs"
                        )
                        test_log_path = gr.Textbox(
                            label="Results Directory",
                            placeholder="e.g., ./test-reports/exploratory",
                            value="./test-reports/exploratory",
                            info="Directory to save test results",
                            interactive=True
                        )

                    with gr.Row():
                        headless = gr.Checkbox(
                            label="Headless Mode",
                            value=False,
                            info="Run browser in headless mode"
                        )
                        window_w = gr.Number(
                            label="Window Width",
                            value=1920,
                            info="Browser window width"
                        )
                        window_h = gr.Number(
                            label="Window Height",
                            value=1080,
                            info="Browser window height"
                        )

                    with gr.Row():
                        run_test_button = gr.Button("▶️ Run Test", variant="primary", scale=2)
                        clear_test_button = gr.Button("🗑️ Clear", variant="secondary", scale=1)

                    gr.Markdown("### Test Results")
                    with gr.Row():
                        test_status = gr.Textbox(
                            label="Status",
                            interactive=False
                        )
                        test_duration = gr.Textbox(
                            label="Duration",
                            interactive=False
                        )

                    test_output = gr.Markdown(
                        label="Test Output",
                        value="",
                        show_label=True
                    )

                    browser_view = gr.HTML(
                        value="<h1 style='width:80vw; height:50vh'>Waiting for browser session...</h1>",
                        label="Live Browser View",
                        visible=True
                    )

                    test_recording = gr.Video(
                        label="Test Recording",
                        visible=True
                    )

                    async def run_exploratory_test(
                        test_name, test_category, starting_url,
                        test_task, test_log_level,
                        enable_test_logging, test_log_path,
                        headless, window_w, window_h
                    ):
                        try:
                            # Create results directory
                            if enable_test_logging:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                test_dir = os.path.join(test_log_path, f"{test_name}_{timestamp}")
                                os.makedirs(test_dir, exist_ok=True)

                                # Save test metadata
                                metadata = {
                                    "name": test_name,
                                    "category": test_category,
                                    "starting_url": starting_url,
                                    "task": test_task,
                                    "timestamp": timestamp
                                }
                                with open(os.path.join(test_dir, "test_info.json"), "w") as f:
                                    json.dump(metadata, f, indent=2)

                            # Configure logging
                            if enable_test_logging:
                                log_file = os.path.join(test_dir, "test.log")
                                logging.basicConfig(
                                    level=getattr(logging, test_log_level),
                                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    handlers=[
                                        logging.FileHandler(log_file),
                                        logging.StreamHandler(sys.stdout)
                                    ]
                                )
                            else:
                                logging.basicConfig(
                                    level=getattr(logging, test_log_level),
                                    format='%(levelname)s - %(message)s'
                                )

                            # Initialize LLM using environment variables
                            llm = utils.get_llm_model(
                                provider=os.getenv('TEST_LLM_PROVIDER', 'gemini'),
                                model_name=os.getenv('TEST_LLM_MODEL', 'gemini-2.0-flash-exp'),
                                temperature=0.5,
                                base_url=os.getenv('TEST_LLM_BASE_URL'),
                                api_key=os.getenv('GOOGLE_API_KEY')
                            )

                            # Set up recording path
                            recording_path = os.path.join(test_dir, "recording") if enable_test_logging else None
                            if recording_path:
                                os.makedirs(recording_path, exist_ok=True)

                            # Initialize browser with headless mode and window size
                            browser = Browser(
                                config=BrowserConfig(
                                    headless=headless,
                                    disable_security=False,
                                    extra_chromium_args=[f"--window-size={window_w},{window_h}"]
                                )
                            )

                            browser_context = await browser.new_context(
                                config=BrowserContextConfig(
                                    no_viewport=False,
                                    browser_window_size=BrowserContextWindowSize(
                                        width=window_w,
                                        height=window_h
                                    ),
                                    save_recording_path=recording_path
                                )
                            )

                            # Initialize agent
                            start_time = datetime.now()
                            agent = Agent(
                                task=f"Navigate to {starting_url} and then {test_task}",
                                llm=llm,
                                browser=browser,
                                browser_context=browser_context,
                                use_vision=True
                            )

                            # Stream setup for browser view
                            stream_vw = 80
                            stream_vh = int(80 * window_h // window_w)

                            # Run the test with fixed max_steps and periodic updates
                            history = None
                            try:
                                # Start the agent task
                                agent_task = asyncio.create_task(agent.run(max_steps=10))
                                
                                # Update browser view periodically while agent is running
                                while not agent_task.done():
                                    screenshot = await capture_screenshot(browser_context)
                                    if screenshot:
                                        html_content = f'<img src="data:image/jpeg;base64,{screenshot}" style="width:{stream_vw}vw; height:{stream_vh}vh; border:1px solid #ccc;">'
                                    else:
                                        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Running test...</h1>"
                                    
                                    yield (
                                        "Running",
                                        f"{(datetime.now() - start_time).total_seconds():.2f}s",
                                        "Test in progress...",
                                        html_content,
                                        None
                                    )
                                    await asyncio.sleep(0.1)  # Update every 100ms
                                
                                # Get the agent results
                                history = await agent_task

                            except Exception as e:
                                error_msg = f"Agent execution failed: {str(e)}"
                                logging.error(error_msg)
                                yield (
                                    "Error",
                                    "0.00s",
                                    f"### Test Error\n{error_msg}",
                                    f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Test failed</h1>",
                                    None
                                )
                                return

                            duration = (datetime.now() - start_time).total_seconds()

                            # Process results
                            success = not history.errors()
                            status = "Passed" if success else "Failed"
                            result_message = []
                            result_message.append(f"### Test Results for: {test_name}\n")
                            result_message.append(f"**Status:** {status}")
                            result_message.append(f"**Duration:** {duration:.2f}s\n")
                            
                            if history.errors():
                                result_message.append("**Errors:**")
                                for error in history.errors():
                                    result_message.append(f"- {str(error)}")
                            
                            result_message.append("\n**Actions Taken:**")
                            for action in history.model_actions():
                                result_message.append(f"- {str(action)}")
                            
                            result_message.append("\n**Agent Thoughts:**")
                            for thought in history.model_thoughts():
                                result_message.append(f"- {str(thought)}")

                            # Save results if enabled
                            if enable_test_logging:
                                with open(os.path.join(test_dir, "test_results.json"), "w") as f:
                                    json.dump({
                                        "status": status,
                                        "duration": duration,
                                        "errors": [str(e) for e in history.errors()],
                                        "actions": [str(a) for a in history.model_actions()],
                                        "thoughts": [str(t) for t in history.model_thoughts()],
                                        "final_result": str(history.final_result())
                                    }, f, indent=2)

                            # Get the recording file if it exists
                            recording_file = None
                            if recording_path:
                                recording_files = glob.glob(os.path.join(recording_path, "*.[mM][pP]4")) + \
                                                glob.glob(os.path.join(recording_path, "*.[wW][eE][bB][mM]"))
                                if recording_files:
                                    recording_file = recording_files[0]

                            # Get final screenshot
                            final_screenshot = await capture_screenshot(browser_context)
                            if final_screenshot:
                                html_content = f'<img src="data:image/jpeg;base64,{final_screenshot}" style="width:{stream_vw}vw; height:{stream_vh}vh; border:1px solid #ccc;">'
                            else:
                                html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Test completed</h1>"

                            # Clean up browser
                            await browser_context.close()
                            await browser.close()

                            yield (
                                status,
                                f"{duration:.2f}s",
                                "\n".join(result_message),
                                html_content,
                                recording_file
                            )

                        except Exception as e:
                            error_msg = f"Test execution failed: {str(e)}"
                            logging.error(error_msg)
                            yield (
                                "Error",
                                "0.00s",
                                f"### Test Error\n{error_msg}",
                                f"<h1 style='width:80vw; height:50vh'>Test failed</h1>",
                                None
                            )

                    def clear_test_form():
                        return [
                            "",  # test_name
                            "Navigation",  # test_category
                            "https://www.google.com",  # starting_url
                            "",  # test_task
                            "",  # test_status
                            "",  # test_duration
                            "",  # test_output
                            None,  # test_recording
                            "<h1 style='width:80vw; height:50vh'>Waiting for browser session...</h1>"  # browser_view
                        ]

                    # Connect event handlers
                    run_test_button.click(
                        fn=run_exploratory_test,
                        inputs=[
                            test_name, test_category, starting_url,
                            test_task, test_log_level,
                            enable_test_logging, test_log_path,
                            headless, window_w, window_h
                        ],
                        outputs=[test_status, test_duration, test_output, browser_view, test_recording]
                    )

                    clear_test_button.click(
                        fn=clear_test_form,
                        inputs=[],
                        outputs=[
                            test_name, test_category, starting_url,
                            test_task, test_status, test_duration,
                            test_output, test_recording, browser_view
                        ]
                    )

                    enable_test_logging.change(
                        lambda enabled: gr.update(interactive=enabled),
                        inputs=[enable_test_logging],
                        outputs=[test_log_path]
                    )

            with gr.TabItem("⚙️ Agent Settings", id=3):
                with gr.Group():
                    agent_type = gr.Radio(
                        ["org", "custom"],
                        label="Agent Type",
                        value=config['agent_type'],
                        info="Select the type of agent to use",
                    )
                    with gr.Column():
                        max_steps = gr.Slider(
                            minimum=1,
                            maximum=200,
                            value=config['max_steps'],
                            step=1,
                            label="Max Run Steps",
                            info="Maximum number of steps the agent will take",
                        )
                        max_actions_per_step = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=config['max_actions_per_step'],
                            step=1,
                            label="Max Actions per Step",
                            info="Maximum number of actions the agent will take per step",
                        )
                    with gr.Column():
                        use_vision = gr.Checkbox(
                            label="Use Vision",
                            value=config['use_vision'],
                            info="Enable visual processing capabilities",
                        )
                        tool_calling_method = gr.Dropdown(
                            label="Tool Calling Method",
                            value=config['tool_calling_method'],
                            interactive=True,
                            allow_custom_value=True,  # Allow users to input custom model names
                            choices=["auto", "json_schema", "function_calling"],
                            info="Tool Calls Funtion Name",
                            visible=False
                        )

            with gr.TabItem("🔧 LLM Configuration", id=4):
                with gr.Group():
                    llm_provider = gr.Dropdown(
                        choices=[provider for provider,model in utils.model_names.items()],
                        label="LLM Provider",
                        value=config['llm_provider'],
                        info="Select your preferred language model provider"
                    )
                    llm_model_name = gr.Dropdown(
                        label="Model Name",
                        choices=utils.model_names['openai'],
                        value=config['llm_model_name'],
                        interactive=True,
                        allow_custom_value=True,  # Allow users to input custom model names
                        info="Select a model from the dropdown or type a custom model name"
                    )
                    llm_temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=config['llm_temperature'],
                        step=0.1,
                        label="Temperature",
                        info="Controls randomness in model outputs"
                    )
                    with gr.Row():
                        llm_base_url = gr.Textbox(
                            label="Base URL",
                            value=config['llm_base_url'],
                            info="API endpoint URL (if required)"
                        )
                        llm_api_key = gr.Textbox(
                            label="API Key",
                            type="password",
                            value=config['llm_api_key'],
                            info="Your API key (leave blank to use .env)"
                        )

            with gr.TabItem("🌐 Browser Settings", id=5):
                with gr.Group():
                    with gr.Row():
                        use_own_browser = gr.Checkbox(
                            label="Use Own Browser",
                            value=config['use_own_browser'],
                            info="Use your existing browser instance",
                        )
                        keep_browser_open = gr.Checkbox(
                            label="Keep Browser Open",
                            value=config['keep_browser_open'],
                            info="Keep Browser Open between Tasks",
                        )
                        headless = gr.Checkbox(
                            label="Headless Mode",
                            value=config['headless'],
                            info="Run browser without GUI",
                        )
                        disable_security = gr.Checkbox(
                            label="Disable Security",
                            value=config['disable_security'],
                            info="Disable browser security features",
                        )
                        enable_recording = gr.Checkbox(
                            label="Enable Recording",
                            value=config['enable_recording'],
                            info="Enable saving browser recordings",
                        )

                    with gr.Row():
                        window_w = gr.Number(
                            label="Window Width",
                            value=config['window_w'],
                            info="Browser window width",
                        )
                        window_h = gr.Number(
                            label="Window Height",
                            value=config['window_h'],
                            info="Browser window height",
                        )

                    save_recording_path = gr.Textbox(
                        label="Recording Path",
                        placeholder="e.g. ./tmp/record_videos",
                        value=config['save_recording_path'],
                        info="Path to save browser recordings",
                        interactive=True,  # Allow editing only if recording is enabled
                    )

                    save_trace_path = gr.Textbox(
                        label="Trace Path",
                        placeholder="e.g. ./tmp/traces",
                        value=config['save_trace_path'],
                        info="Path to save Agent traces",
                        interactive=True,
                    )

                    save_agent_history_path = gr.Textbox(
                        label="Agent History Save Path",
                        placeholder="e.g., ./tmp/agent_history",
                        value=config['save_agent_history_path'],
                        info="Specify the directory where agent history should be saved.",
                        interactive=True,
                    )

            with gr.TabItem("🤖 Run Agent", id=6):
                task = gr.Textbox(
                    label="Task Description",
                    lines=4,
                    placeholder="Enter your task here...",
                    value=config['task'],
                    info="Describe what you want the agent to do",
                )
                add_infos = gr.Textbox(
                    label="Additional Information",
                    lines=3,
                    placeholder="Add any helpful context or instructions...",
                    info="Optional hints to help the LLM complete the task",
                )

                with gr.Row():
                    run_button = gr.Button("▶️ Run Agent", variant="primary", scale=2)
                    stop_button = gr.Button("⏹️ Stop", variant="stop", scale=1)
                    
                with gr.Row():
                    browser_view = gr.HTML(
                        value="<h1 style='width:80vw; height:50vh'>Waiting for browser session...</h1>",
                        label="Live Browser View",
                )

            with gr.TabItem("📁 Configuration", id=7):
                with gr.Group():
                    config_file_input = gr.File(
                        label="Load Config File",
                        file_types=[".pkl"],
                        interactive=True
                    )

                    load_config_button = gr.Button("Load Existing Config From File", variant="primary")
                    save_config_button = gr.Button("Save Current Config", variant="primary")

                    config_status = gr.Textbox(
                        label="Status",
                        lines=2,
                        interactive=False
                    )

                load_config_button.click(
                    fn=update_ui_from_config,
                    inputs=[config_file_input],
                    outputs=[
                        agent_type, max_steps, max_actions_per_step, use_vision, tool_calling_method,
                        llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                        use_own_browser, keep_browser_open, headless, disable_security, enable_recording,
                        window_w, window_h, save_recording_path, save_trace_path, save_agent_history_path,
                        task, config_status
                    ]
                )

                save_config_button.click(
                    fn=save_current_config,
                    inputs=[
                        agent_type, max_steps, max_actions_per_step, use_vision, tool_calling_method,
                        llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                        use_own_browser, keep_browser_open, headless, disable_security,
                        enable_recording, window_w, window_h, save_recording_path, save_trace_path,
                        save_agent_history_path, task,
                    ],  
                    outputs=[config_status]
                )

            with gr.TabItem("📊 Results", id=8):
                with gr.Group():

                    recording_display = gr.Video(label="Latest Recording")

                    gr.Markdown("### Results")
                    with gr.Row():
                        with gr.Column():
                            final_result_output = gr.Textbox(
                                label="Final Result", lines=3, show_label=True
                            )
                        with gr.Column():
                            errors_output = gr.Textbox(
                                label="Errors", lines=3, show_label=True
                            )
                    with gr.Row():
                        with gr.Column():
                            model_actions_output = gr.Textbox(
                                label="Model Actions", lines=3, show_label=True
                            )
                        with gr.Column():
                            model_thoughts_output = gr.Textbox(
                                label="Model Thoughts", lines=3, show_label=True
                            )

                    trace_file = gr.File(label="Trace File")

                    agent_history_file = gr.File(label="Agent History")

                # Bind the stop button click event after errors_output is defined
                stop_button.click(
                    fn=stop_agent,
                    inputs=[],
                    outputs=[errors_output, stop_button, run_button],
                )

                # Run button click handler
                run_button.click(
                    fn=run_with_stream,
                        inputs=[
                            agent_type, llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                            use_own_browser, keep_browser_open, headless, disable_security, window_w, window_h,
                            save_recording_path, save_agent_history_path, save_trace_path,  # Include the new path
                            enable_recording, task, add_infos, max_steps, use_vision, max_actions_per_step, tool_calling_method
                        ],
                    outputs=[
                        browser_view,           # Browser view
                        final_result_output,    # Final result
                        errors_output,          # Errors
                        model_actions_output,   # Model actions
                        model_thoughts_output,  # Model thoughts
                        recording_display,      # Latest recording
                        trace_file,             # Trace file
                        agent_history_file,     # Agent history file
                        stop_button,            # Stop button
                        run_button              # Run button
                    ],
                )

            with gr.TabItem("🎥 Recordings", id=9):
                def list_recordings(save_recording_path):
                    if not os.path.exists(save_recording_path):
                        return []

                    # Get all video files
                    recordings = glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4")) + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))

                    # Sort recordings by creation time (oldest first)
                    recordings.sort(key=os.path.getctime)

                    # Add numbering to the recordings
                    numbered_recordings = []
                    for idx, recording in enumerate(recordings, start=1):
                        filename = os.path.basename(recording)
                        numbered_recordings.append((recording, f"{idx}. {filename}"))

                    return numbered_recordings

                recordings_gallery = gr.Gallery(
                    label="Recordings",
                    value=list_recordings(config['save_recording_path']),
                    columns=3,
                    height="auto",
                    object_fit="contain"
                )

                refresh_button = gr.Button("🔄 Refresh Recordings", variant="secondary")
                refresh_button.click(
                    fn=list_recordings,
                    inputs=save_recording_path,
                    outputs=recordings_gallery
                )

        # Attach the callback to the LLM provider dropdown
        llm_provider.change(
            lambda provider, api_key, base_url: update_model_dropdown(provider, api_key, base_url),
            inputs=[llm_provider, llm_api_key, llm_base_url],
            outputs=llm_model_name
        )

        # Add this after defining the components
        enable_recording.change(
            lambda enabled: gr.update(interactive=enabled),
            inputs=enable_recording,
            outputs=save_recording_path
        )

        use_own_browser.change(fn=close_global_browser)
        keep_browser_open.change(fn=close_global_browser)

    return demo

def main():
    parser = argparse.ArgumentParser(description="Gradio UI for Browser Agent")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    parser.add_argument("--dark-mode", action="store_true", help="Enable dark mode")
    args = parser.parse_args()

    config_dict = default_config()

    demo = create_ui(config_dict, theme_name=args.theme)
    demo.launch(server_name=args.ip, server_port=args.port)

if __name__ == '__main__':
    main()
