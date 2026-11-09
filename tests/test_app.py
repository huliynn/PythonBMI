import unittest

from app import app, bmi_guidance


class BmiAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_initial_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("了解自己的<br><em>健康狀況。</em>", page)
        self.assertIn("計算你的 BMI", page)
        self.assertIn('name="name"', page)

    def test_calculation_and_advice(self):
        response = self.client.post("/", data={"height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn("22.5", page)
        self.assertIn("健康體位", page)
        self.assertIn("維持均衡飲食", page)
        self.assertIn('class="bmi-gauge"', page)
        self.assertIn("目前 BMI 22.5", page)
        self.assertIn("style=\"transform: rotate(-15.0deg)\"", page)
        self.assertIn("健康提醒", page)

    def test_name_is_included_in_advice(self):
        response = self.client.post("/", data={"name": "小明", "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn("<p>小明，維持均衡飲食", page)

    def test_name_is_preserved_when_measurements_are_invalid(self):
        response = self.client.post("/", data={"name": "小明", "height": "", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn('value="小明"', page)

    def test_gauge_pointer_is_clamped_to_scale(self):
        for weight, angle in [("10", "-90.0"), ("300", "90.0")]:
            with self.subTest(weight=weight):
                response = self.client.post("/", data={"height": "100", "weight": weight})
                self.assertIn(f"rotate({angle}deg)", response.get_data(as_text=True))

    def test_taiwan_adult_thresholds(self):
        for bmi, category in [
            (18.4, "體重過輕"),
            (18.5, "健康體位"),
            (23.9, "健康體位"),
            (24.0, "體重過重"),
            (26.9, "體重過重"),
            (27.0, "肥胖"),
        ]:
            with self.subTest(bmi=bmi):
                self.assertEqual(bmi_guidance(bmi)["label"], category)

    def test_invalid_fields_do_not_produce_result(self):
        for height, weight in [("", "65"), ("0", "65"), ("abc", "65"), ("170", "-2"), ("inf", "65"), ("170", "nan"), ("1e-300", "65"), ("1e308", "65"), ("1", "1e308")]:
            with self.subTest(height=height, weight=weight):
                response = self.client.post("/", data={"height": height, "weight": weight})
                page = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn('aria-invalid="true"', page)
                self.assertNotIn("YOUR RESULT", page)

    def test_input_is_escaped(self):
        response = self.client.post("/", data={"height": '<script>alert(1)</script>', "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertNotIn("<script>", page)
        self.assertIn("請輸入大於 0", page)

    def test_name_is_escaped_in_advice(self):
        response = self.client.post("/", data={"name": "<script>alert(1)</script>", "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;，維持均衡飲食", page)
        self.assertNotIn("<script>alert(1)</script>", page)


if __name__ == "__main__":
    unittest.main()
