#!/usr/bin/env python3
"""
Comprehensive Test Suite for LanguageDetector

Tests confidence-based language detection for 20+ programming languages.
Includes Unity C# patterns, CSS class detection, and edge cases.

Run with: pytest tests/test_language_detector.py -v
"""

import pytest
from bs4 import BeautifulSoup
from skill_seekers.cli.language_detector import LanguageDetector


class TestCSSClassDetection:
    """Test language detection from CSS classes"""

    def test_language_prefix(self):
        """Test language- prefix pattern"""
        detector = LanguageDetector()

        classes = ['language-python', 'highlight']
        assert detector.extract_language_from_classes(classes) == 'python'

        classes = ['language-javascript']
        assert detector.extract_language_from_classes(classes) == 'javascript'

    def test_lang_prefix(self):
        """Test lang- prefix pattern"""
        detector = LanguageDetector()

        classes = ['lang-java', 'code']
        assert detector.extract_language_from_classes(classes) == 'java'

        classes = ['lang-typescript']
        assert detector.extract_language_from_classes(classes) == 'typescript'

    def test_brush_pattern(self):
        """Test brush: pattern"""
        detector = LanguageDetector()

        classes = ['brush: php']
        assert detector.extract_language_from_classes(classes) == 'php'

        classes = ['brush: csharp']
        assert detector.extract_language_from_classes(classes) == 'csharp'

    def test_bare_class_name(self):
        """Test bare language name as class"""
        detector = LanguageDetector()

        classes = ['python', 'highlight']
        assert detector.extract_language_from_classes(classes) == 'python'

        classes = ['rust']
        assert detector.extract_language_from_classes(classes) == 'rust'

    def test_unknown_language(self):
        """Test unknown language class"""
        detector = LanguageDetector()

        classes = ['language-foobar']
        assert detector.extract_language_from_classes(classes) is None

        classes = ['highlight', 'code']
        assert detector.extract_language_from_classes(classes) is None

    def test_empty_classes(self):
        """Test empty class list"""
        detector = LanguageDetector()

        assert detector.extract_language_from_classes([]) is None
        assert detector.extract_language_from_classes(None) is None

    def test_detect_from_html_with_css_class(self):
        """Test HTML element with CSS class"""
        detector = LanguageDetector()

        # Create mock element
        html = '<code class="language-python">print("hello")</code>'
        soup = BeautifulSoup(html, 'html.parser')
        elem = soup.find('code')

        lang, confidence = detector.detect_from_html(elem, 'print("hello")')
        assert lang == 'python'
        assert confidence == 1.0  # CSS class = high confidence

    def test_detect_from_html_with_parent_class(self):
        """Test parent <pre> element with CSS class"""
        detector = LanguageDetector()

        # Parent has class, child doesn't
        html = '<pre class="language-java"><code>System.out.println("hello");</code></pre>'
        soup = BeautifulSoup(html, 'html.parser')
        elem = soup.find('code')

        lang, confidence = detector.detect_from_html(elem, 'System.out.println("hello");')
        assert lang == 'java'
        assert confidence == 1.0


class TestUnityCSharpDetection:
    """Test Unity C# specific patterns (CRITICAL - User's Primary Issue)"""

    def test_unity_monobehaviour_detection(self):
        """Test Unity MonoBehaviour class detection"""
        detector = LanguageDetector()

        code = """
        using UnityEngine;

        public class Player : MonoBehaviour
        {
            [SerializeField]
            private float speed = 5.0f;

            void Start() { }
            void Update() { }
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.9  # High confidence (Unity patterns)

    def test_unity_lifecycle_methods(self):
        """Test Unity lifecycle method detection"""
        detector = LanguageDetector()

        code = """
        void Awake() { }
        void Start() { }
        void Update() { }
        void FixedUpdate() { }
        void LateUpdate() { }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.5

    def test_unity_coroutine_detection(self):
        """Test Unity coroutine detection"""
        detector = LanguageDetector()

        code = """
        IEnumerator Wait()
        {
            yield return new WaitForSeconds(1);
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.4

    def test_unity_serializefield_attribute(self):
        """Test Unity attribute detection"""
        detector = LanguageDetector()

        code = """
        [SerializeField]
        private GameObject player;

        [RequireComponent(typeof(Rigidbody))]
        public class Test : MonoBehaviour { }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.7

    def test_unity_types(self):
        """Test Unity type detection (GameObject, Transform, etc.)"""
        detector = LanguageDetector()

        code = """
        GameObject obj = new GameObject();
        Transform transform = obj.transform;
        Vector3 position = transform.position;
        Rigidbody rb = obj.GetComponent<Rigidbody>();
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.3

    def test_unity_namespace(self):
        """Test Unity namespace detection"""
        detector = LanguageDetector()

        code = "using UnityEngine;"
        lang, confidence = detector.detect_from_code(code)

        # Short code, but very specific Unity pattern (19 chars)
        # Now detects due to lowered min length threshold (10 chars)
        assert lang == 'csharp'
        assert confidence >= 0.5

        # Longer version
        code = """
        using UnityEngine;
        using System.Collections;
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.5

    def test_generic_csharp_vs_unity(self):
        """Test generic C# doesn't false-positive as Unity"""
        detector = LanguageDetector()

        # Generic C# code
        code = """
        using System;

        public class Program
        {
            static void Main(string[] args)
            {
                Console.WriteLine("Hello");
            }
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        # Confidence should be high (contains multiple C# patterns)
        # No Unity-specific patterns, but Console.WriteLine is strong indicator
        assert 0.7 <= confidence <= 1.0

    def test_unity_minimal_code(self):
        """Test minimal Unity code (edge case)"""
        detector = LanguageDetector()

        code = "void Update() { Time.deltaTime; }"
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.3  # Low but detected

    def test_unity_input_system(self):
        """Test Unity Input system detection"""
        detector = LanguageDetector()

        code = """
        float horizontal = Input.GetAxis("Horizontal");
        if (Input.GetKeyDown(KeyCode.Space)) { }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.4

    def test_unity_full_script(self):
        """Test complete Unity script (high confidence expected)"""
        detector = LanguageDetector()

        code = """
        using UnityEngine;
        using System.Collections;

        public class PlayerController : MonoBehaviour
        {
            [SerializeField]
            private float speed = 5.0f;

            [SerializeField]
            private Rigidbody rb;

            void Awake()
            {
                rb = GetComponent<Rigidbody>();
            }

            void Update()
            {
                float moveH = Input.GetAxis("Horizontal");
                float moveV = Input.GetAxis("Vertical");

                Vector3 movement = new Vector3(moveH, 0, moveV);
                rb.AddForce(movement * speed);
            }

            IEnumerator DashCoroutine()
            {
                speed *= 2;
                yield return new WaitForSeconds(0.5f);
                speed /= 2;
            }
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'csharp'
        assert confidence >= 0.9  # Very high confidence (many Unity patterns)


class TestLanguageDetection:
    """Test detection for major programming languages"""

    def test_python_detection(self):
        """Test Python code detection"""
        detector = LanguageDetector()

        code = """
        def calculate(x, y):
            result = x + y
            return result

        class MyClass:
            def __init__(self):
                self.value = 0
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'python'
        assert confidence >= 0.5

    def test_javascript_detection(self):
        """Test JavaScript code detection"""
        detector = LanguageDetector()

        code = """
        const add = (a, b) => a + b;

        function calculate() {
            let result = 0;
            console.log(result);
            return result;
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'javascript'
        assert confidence >= 0.5

    def test_typescript_detection(self):
        """Test TypeScript code detection"""
        detector = LanguageDetector()

        code = """
        interface User {
            name: string;
            age: number;
        }

        type ID = string | number;

        function getUser(): User {
            return { name: "John", age: 30 };
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'typescript'
        assert confidence >= 0.7

    def test_java_detection(self):
        """Test Java code detection"""
        detector = LanguageDetector()

        code = """
        public class Hello {
            public static void main(String[] args) {
                System.out.println("Hello World");
            }
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'java'
        assert confidence >= 0.6

    def test_go_detection(self):
        """Test Go code detection"""
        detector = LanguageDetector()

        code = """
        package main

        import "fmt"

        func main() {
            message := "Hello, World"
            fmt.Println(message)
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'go'
        assert confidence >= 0.6

    def test_rust_detection(self):
        """Test Rust code detection"""
        detector = LanguageDetector()

        code = """
        fn main() {
            let mut x = 5;
            println!("The value is: {}", x);

            match x {
                1 => println!("One"),
                _ => println!("Other"),
            }
        }
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'rust'
        assert confidence >= 0.6

    def test_php_detection(self):
        """Test PHP code detection"""
        detector = LanguageDetector()

        code = """
        <?php
        class User {
            public function getName() {
                return $this->name;
            }
        }
        ?>
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'php'
        assert confidence >= 0.7

    def test_jsx_detection(self):
        """Test JSX code detection"""
        detector = LanguageDetector()

        code = """
        const Button = () => {
            const [count, setCount] = useState(0);

            return (
                <button onClick={() => setCount(count + 1)}>
                    Click me: {count}
                </button>
            );
        };
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'jsx'
        assert confidence >= 0.5

    def test_vue_detection(self):
        """Test Vue SFC detection"""
        detector = LanguageDetector()

        code = """
        <template>
            <div>{{ message }}</div>
        </template>

        <script>
        export default {
            data() {
                return { message: "Hello" };
            }
        }
        </script>
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'vue'
        assert confidence >= 0.7

    def test_sql_detection(self):
        """Test SQL code detection"""
        detector = LanguageDetector()

        code = """
        SELECT users.name, orders.total
        FROM users
        JOIN orders ON users.id = orders.user_id
        WHERE orders.status = 'completed'
        ORDER BY orders.total DESC;
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'sql'
        assert confidence >= 0.6


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_short_code_snippet(self):
        """Test code snippet too short for detection"""
        detector = LanguageDetector()

        code = "x = 5"
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'unknown'
        assert confidence == 0.0

    def test_empty_code(self):
        """Test empty code string"""
        detector = LanguageDetector()

        lang, confidence = detector.detect_from_code("")
        assert lang == 'unknown'
        assert confidence == 0.0

    def test_whitespace_only(self):
        """Test whitespace-only code"""
        detector = LanguageDetector()

        code = "    \n    \n    "
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'unknown'
        assert confidence == 0.0

    def test_comments_only(self):
        """Test code with only comments"""
        detector = LanguageDetector()

        code = """
        // This is a comment
        // Another comment
        /* More comments */
        """

        lang, confidence = detector.detect_from_code(code)
        # Should return unknown or very low confidence
        assert confidence < 0.5

    def test_mixed_languages(self):
        """Test code with multiple language patterns"""
        detector = LanguageDetector()

        # HTML with embedded JavaScript
        code = """
        <script>
        function test() {
            console.log("test");
        }
        </script>
        """

        lang, confidence = detector.detect_from_code(code)
        # Should detect strongest pattern
        # Both html and javascript patterns present
        assert lang in ['html', 'javascript']

    def test_confidence_threshold(self):
        """Test minimum confidence threshold"""
        # Create detector with high threshold
        detector = LanguageDetector(min_confidence=0.7)

        # Code with weak patterns (low confidence)
        code = "var x = 5; const y = 10;"

        lang, confidence = detector.detect_from_code(code)

        # If confidence < 0.7, should return unknown
        if confidence < 0.7:
            assert lang == 'unknown'

    def test_html_with_embedded_css(self):
        """Test HTML with embedded CSS"""
        detector = LanguageDetector()

        code = """
        <style>
        .container {
            display: flex;
            margin: 0 auto;
        }
        </style>
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang in ['html', 'css']

    def test_case_insensitive_patterns(self):
        """Test that patterns are case-insensitive"""
        detector = LanguageDetector()

        # SQL with different cases
        code = """
        select users.name
        FROM users
        where users.status = 'active'
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'sql'

    def test_r_language_detection(self):
        """Test R language detection (edge case: single letter)"""
        detector = LanguageDetector()

        code = """
        library(ggplot2)
        data <- read.csv("data.csv")
        summary(data)

        ggplot(data, aes(x = x, y = y)) +
            geom_point()
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'r'
        assert confidence >= 0.5

    def test_julia_detection(self):
        """Test Julia language detection"""
        detector = LanguageDetector()

        code = """
        function calculate(x, y)
            result = x + y
            return result
        end

        using Statistics
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'julia'
        assert confidence >= 0.3

    def test_gdscript_detection(self):
        """Test GDScript (Godot) detection"""
        detector = LanguageDetector()

        code = """
        extends Node2D

        var speed = 100

        func _ready():
            pass

        func _process(delta):
            position.x += speed * delta
        """

        lang, confidence = detector.detect_from_code(code)
        assert lang == 'gdscript'
        assert confidence >= 0.5

    def test_multiple_confidence_scores(self):
        """Test that multiple languages can have scores"""
        detector = LanguageDetector()

        # Code that matches both C# and Java patterns
        code = """
        public class Test {
            public static void main() {
                System.out.println("hello");
            }
        }
        """

        lang, confidence = detector.detect_from_code(code)
        # Should detect the one with highest confidence
        assert lang in ['csharp', 'java']
        assert confidence > 0.0


class TestIntegration:
    """Integration tests with doc_scraper patterns"""

    def test_detect_from_html_fallback_to_patterns(self):
        """Test fallback from CSS classes to pattern matching"""
        detector = LanguageDetector()

        # Element without CSS classes
        html = '<code>def test(): pass</code>'
        soup = BeautifulSoup(html, 'html.parser')
        elem = soup.find('code')

        lang, confidence = detector.detect_from_html(elem, 'def test(): pass')
        # Should fallback to pattern matching
        # Now detects due to lowered min length threshold (10 chars)
        assert lang == 'python'
        assert confidence >= 0.2

    def test_backward_compatibility_with_doc_scraper(self):
        """Test that detector can be used as drop-in replacement"""
        detector = LanguageDetector()

        # Simulate doc_scraper.py usage
        html = '<code class="language-python">import os\nprint("hello")</code>'
        soup = BeautifulSoup(html, 'html.parser')
        elem = soup.find('code')
        code = elem.get_text()

        # This is how doc_scraper.py would call it
        lang, confidence = detector.detect_from_html(elem, code)

        # Should work exactly as before (returning string)
        assert isinstance(lang, str)
        assert isinstance(confidence, float)
        assert lang == 'python'
        assert 0.0 <= confidence <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
