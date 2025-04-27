from selenium import webdriver

def test_homepage():
    driver = webdriver.Chrome()
    driver.get("http://localhost:5000")
    assert "Welcome" in driver.title
    driver.quit()