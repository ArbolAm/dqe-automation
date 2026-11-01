import time
import os
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)


class SeleniumWebDriverContextManager:
    def __init__(self):
        self.driver = None

    def __enter__(self):
        self.driver = webdriver.Chrome()
        return self.driver

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver is not None:
            self.driver.quit()


def save_doughnut_state(
    driver, graph, pie_layer, screenshots_dir, output_files_dir, index
):
    chart_state = driver.execute_script(
        """
        const graph = arguments[0];
        const pie = graph._fullData.find(trace => trace.type === "pie");
        if (!pie) return null;
        return {
            labels: Array.from(pie.labels),
            values: Array.from(pie.values),
            hidden: Array.from(graph._fullLayout.hiddenlabels || [])
        };
        """,
        graph,
    )
    if chart_state is None:
        raise NoSuchElementException("The report has no doughnut chart")

    visible_rows = [
        (label, value)
        for label, value in zip(chart_state["labels"], chart_state["values"])
        if label not in chart_state["hidden"]
    ]
    pd.DataFrame(
        visible_rows,
        columns=["Facility Type", "Min Average Time Spent"],
    ).to_csv(os.path.join(output_files_dir, f"doughnut{index}.csv"), index=False)
    screenshot_path = os.path.join(screenshots_dir, f"screenshot{index}.png")
    if pie_layer.rect["width"] and pie_layer.rect["height"]:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", pie_layer
        )
        pie_layer.screenshot(screenshot_path)
    else:
        graph.screenshot(screenshot_path)


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    report_path = os.path.join(base_dir, "report.html")
    screenshots_dir = os.path.join(base_dir, "screenshots")
    output_files_dir = os.path.join(base_dir, "output_files")
    csv_path = os.path.join(output_files_dir, "table.csv")
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(output_files_dir, exist_ok=True)

    try:
        with SeleniumWebDriverContextManager() as driver:
            report_url = "file:///" + os.path.abspath(report_path).replace("\\", "/")
            driver.get(report_url)

            graph = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.plotly-graph-div")
                )
            )
            graph = driver.find_element(By.ID, graph.get_attribute("id"))

            table = WebDriverWait(driver, 15).until(
                lambda browser: graph.find_element(
                    By.XPATH,
                    ".//*[local-name()='g' and contains(concat(' ', normalize-space(@class), ' '), ' table ')]",
                )
            )
            columns = WebDriverWait(driver, 15).until(
                lambda browser: (
                    table.find_elements(By.CLASS_NAME, "y-column")
                    if len(table.find_elements(By.CLASS_NAME, "y-column")) == 3
                    else False
                )
            )
            if not columns:
                raise NoSuchElementException("The report table has no columns")

            headers = []
            column_values = []
            for column in columns:
                cells = column.find_elements(By.CLASS_NAME, "cell-text")
                if not cells:
                    raise NoSuchElementException("A table column has no cell text")
                headers.append(cells[-1].text)
                column_values.append([cell.text for cell in cells[:-1]])

            table_saved = False
            try:
                pd.DataFrame(dict(zip(headers, column_values))).to_csv(
                    csv_path,
                    index=False,
                )
                table_saved = True
            except OSError as error:
                print(f"Could not update the existing table CSV: {error}")

            pie_layer = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "g.pielayer"))
            )
            legend_items = WebDriverWait(driver, 15).until(
                lambda browser: graph.find_elements(
                    By.CSS_SELECTOR, "g.legend g.traces"
                )
                or False
            )
            filter_labels = [item.text.strip() for item in legend_items if item.text.strip()]
            if not filter_labels:
                raise NoSuchElementException("The doughnut chart has no filter options")

            state_index = 0
            save_doughnut_state(
                driver,
                graph,
                pie_layer,
                screenshots_dir,
                output_files_dir,
                state_index,
            )

            for filter_label in filter_labels:
                try:
                    filter_option = WebDriverWait(driver, 10).until(
                        lambda browser: next(
                            (
                                item
                                for item in graph.find_elements(
                                    By.CSS_SELECTOR, "g.legend g.traces"
                                )
                                if item.text.strip() == filter_label
                            ),
                            False,
                        )
                    )
                    filter_option.click()
                    WebDriverWait(driver, 10).until(
                        lambda browser: filter_label
                        in browser.execute_script(
                            "return arguments[0]._fullLayout.hiddenlabels || [];",
                            graph,
                        )
                    )
                    next_index = state_index + 1
                    save_doughnut_state(
                        driver,
                        graph,
                        pie_layer,
                        screenshots_dir,
                        output_files_dir,
                        next_index,
                    )
                    state_index = next_index
                except (NoSuchElementException, TimeoutException, WebDriverException) as error:
                    print(f"Could not apply filter '{filter_label}': {error}")
        if table_saved:
            print(f"Table saved to {csv_path}")
        print(f"Saved {state_index + 1} doughnut screenshots and CSV files")
    except (NoSuchElementException, TimeoutException, OSError, WebDriverException) as error:
        print(f"Could not complete report exports: {error}")
