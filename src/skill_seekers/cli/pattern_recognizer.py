#!/usr/bin/env python3
"""
Design Pattern Recognition Module

Detects common design patterns in codebases across multiple languages.

Supported Patterns:
- Creational: Singleton, Factory, Builder, Prototype
- Structural: Adapter, Decorator, Facade, Proxy
- Behavioral: Observer, Strategy, Command, Template Method, Chain of Responsibility

Detection Levels:
- Surface: Naming conventions (e.g., "Factory", "Singleton")
- Deep: Structural analysis (class relationships, method signatures)
- Full: Behavioral analysis (method interactions, state management)

Credits:
- Design pattern definitions: Gang of Four (GoF) Design Patterns
- Detection heuristics: Inspired by academic research on pattern mining
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import logging
import argparse
import json
import sys

logger = logging.getLogger(__name__)


@dataclass
class PatternInstance:
    """Single detected pattern instance"""
    pattern_type: str  # e.g., 'Singleton', 'Factory'
    category: str  # 'Creational', 'Structural', 'Behavioral'
    confidence: float  # 0.0-1.0
    location: str  # File path
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    line_number: Optional[int] = None
    evidence: List[str] = field(default_factory=list)  # Evidence for detection
    related_classes: List[str] = field(default_factory=list)  # Related pattern classes

    def to_dict(self) -> Dict:
        """Export to dictionary"""
        return {
            'pattern_type': self.pattern_type,
            'category': self.category,
            'confidence': self.confidence,
            'location': self.location,
            'class_name': self.class_name,
            'method_name': self.method_name,
            'line_number': self.line_number,
            'evidence': self.evidence,
            'related_classes': self.related_classes
        }


@dataclass
class PatternReport:
    """Complete pattern detection report"""
    file_path: str
    language: str
    patterns: List[PatternInstance]
    total_classes: int
    total_functions: int
    analysis_depth: str  # 'surface', 'deep', 'full'

    def to_dict(self) -> Dict:
        """Export to dictionary"""
        return {
            'file_path': self.file_path,
            'language': self.language,
            'patterns': [p.to_dict() for p in self.patterns],
            'total_classes': self.total_classes,
            'total_functions': self.total_functions,
            'analysis_depth': self.analysis_depth,
            'pattern_summary': self.get_summary()
        }

    def get_summary(self) -> Dict[str, int]:
        """Get pattern count summary"""
        summary = {}
        for pattern in self.patterns:
            summary[pattern.pattern_type] = summary.get(pattern.pattern_type, 0) + 1
        return summary


class BasePatternDetector:
    """Base class for all pattern detectors"""

    def __init__(self, depth: str = 'deep'):
        """
        Initialize detector.

        Args:
            depth: Detection depth ('surface', 'deep', 'full')
        """
        self.depth = depth
        self.pattern_type = "BasePattern"
        self.category = "Unknown"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """
        Surface-level detection using naming conventions.

        Args:
            class_sig: Class signature to analyze
            all_classes: All classes in the file for context

        Returns:
            PatternInstance if pattern detected, None otherwise
        """
        # Default: no surface detection
        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """
        Deep detection using structural analysis.

        Args:
            class_sig: Class signature to analyze
            all_classes: All classes in the file for context

        Returns:
            PatternInstance if pattern detected, None otherwise
        """
        # Default: no deep detection
        return None

    def detect_full(
        self,
        class_sig,
        all_classes: List,
        file_content: str
    ) -> Optional[PatternInstance]:
        """
        Full detection using behavioral analysis.

        Args:
            class_sig: Class signature to analyze
            all_classes: All classes in the file for context
            file_content: Full file content for advanced analysis

        Returns:
            PatternInstance if pattern detected, None otherwise
        """
        # Default: no full detection
        return None

    def detect(
        self,
        class_sig,
        all_classes: List,
        file_content: Optional[str] = None
    ) -> Optional[PatternInstance]:
        """
        Detect pattern based on configured depth.

        Args:
            class_sig: Class signature to analyze
            all_classes: All classes in the file for context
            file_content: Full file content (needed for 'full' depth)

        Returns:
            PatternInstance if pattern detected, None otherwise
        """
        if self.depth == 'surface':
            return self.detect_surface(class_sig, all_classes)
        elif self.depth == 'deep':
            # Try deep first, fallback to surface
            result = self.detect_deep(class_sig, all_classes)
            if result:
                return result
            return self.detect_surface(class_sig, all_classes)
        elif self.depth == 'full':
            # Try full, fallback to deep, then surface
            if file_content:
                result = self.detect_full(class_sig, all_classes, file_content)
                if result:
                    return result
            result = self.detect_deep(class_sig, all_classes)
            if result:
                return result
            return self.detect_surface(class_sig, all_classes)
        else:
            raise ValueError(f"Invalid depth: {self.depth}")


class PatternRecognizer:
    """
    Main pattern recognition orchestrator.

    Coordinates multiple pattern detectors to analyze code.
    """

    def __init__(self, depth: str = 'deep'):
        """
        Initialize pattern recognizer.

        Args:
            depth: Detection depth ('surface', 'deep', 'full')
        """
        self.depth = depth
        self.detectors: List[BasePatternDetector] = []
        self._register_detectors()

    def _register_detectors(self):
        """Register all available pattern detectors"""
        # Creational patterns (3)
        self.detectors.append(SingletonDetector(self.depth))
        self.detectors.append(FactoryDetector(self.depth))
        self.detectors.append(BuilderDetector(self.depth))

        # Structural patterns (2)
        self.detectors.append(DecoratorDetector(self.depth))
        self.detectors.append(AdapterDetector(self.depth))

        # Behavioral patterns (5)
        self.detectors.append(ObserverDetector(self.depth))
        self.detectors.append(StrategyDetector(self.depth))
        self.detectors.append(CommandDetector(self.depth))
        self.detectors.append(TemplateMethodDetector(self.depth))
        self.detectors.append(ChainOfResponsibilityDetector(self.depth))

    def analyze_file(
        self,
        file_path: str,
        content: str,
        language: str
    ) -> PatternReport:
        """
        Analyze a single file for design patterns.

        Args:
            file_path: Path to source file
            content: File content
            language: Programming language

        Returns:
            PatternReport with detected patterns
        """
        # Step 1: Analyze code structure using CodeAnalyzer
        from skill_seekers.cli.code_analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer(depth='deep')
        analysis = analyzer.analyze_file(file_path, content, language)

        if not analysis:
            return PatternReport(
                file_path=file_path,
                language=language,
                patterns=[],
                total_classes=0,
                total_functions=0,
                analysis_depth=self.depth
            )

        classes = analysis.get('classes', [])
        functions = analysis.get('functions', [])

        # Convert to class signature objects
        class_sigs = self._convert_to_signatures(classes)

        # Step 2: Run pattern detection
        detected_patterns = []

        for class_sig in class_sigs:
            for detector in self.detectors:
                pattern = detector.detect(
                    class_sig=class_sig,
                    all_classes=class_sigs,
                    file_content=content if self.depth == 'full' else None
                )

                if pattern:
                    # Add file path to pattern
                    pattern.location = file_path

                    # Apply language-specific adaptations
                    pattern = LanguageAdapter.adapt_for_language(pattern, language)

                    detected_patterns.append(pattern)

        return PatternReport(
            file_path=file_path,
            language=language,
            patterns=detected_patterns,
            total_classes=len(classes),
            total_functions=len(functions),
            analysis_depth=self.depth
        )

    def _convert_to_signatures(self, classes: List[Dict]):
        """
        Convert dict-based class analysis to signature objects.

        Note: Returns simple namespace objects that mimic ClassSignature structure
        but work with dict-based input from CodeAnalyzer.
        """
        from types import SimpleNamespace

        signatures = []

        for cls in classes:
            # Convert methods
            methods = []
            for method in cls.get('methods', []):
                # Convert parameters
                params = []
                for param in method.get('parameters', []):
                    param_obj = SimpleNamespace(
                        name=param.get('name', ''),
                        type_hint=param.get('type_hint'),
                        default=param.get('default')
                    )
                    params.append(param_obj)

                method_obj = SimpleNamespace(
                    name=method.get('name', ''),
                    parameters=params,
                    return_type=method.get('return_type'),
                    docstring=method.get('docstring'),
                    line_number=method.get('line_number'),
                    is_async=method.get('is_async', False),
                    is_method=True,
                    decorators=method.get('decorators', [])
                )
                methods.append(method_obj)

            class_obj = SimpleNamespace(
                name=cls.get('name', ''),
                base_classes=cls.get('base_classes', []),
                methods=methods,
                docstring=cls.get('docstring'),
                line_number=cls.get('line_number')
            )
            signatures.append(class_obj)

        return signatures


class SingletonDetector(BasePatternDetector):
    """
    Detect Singleton pattern.

    Singleton ensures a class has only one instance and provides global access.

    Detection Heuristics:
    - Surface: Class name contains 'Singleton'
    - Deep: Private constructor + static instance method
    - Full: Instance caching + thread safety checks

    Examples:
    - Python: __new__ override with instance caching
    - JavaScript: Module pattern or class with getInstance()
    - Java: Private constructor + synchronized getInstance()
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "Singleton"
        self.category = "Creational"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check if class name suggests Singleton"""
        if 'singleton' in class_sig.name.lower():
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.6,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=['Class name contains "Singleton"']
            )
        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check structural characteristics of Singleton"""
        evidence = []
        confidence = 0.0

        # Check for instance method (getInstance, instance, get_instance, etc.)
        instance_methods = [
            'getInstance', 'instance', 'get_instance',
            'Instance', 'GetInstance', 'INSTANCE'
        ]

        has_instance_method = False
        for method in class_sig.methods:
            if method.name in instance_methods:
                evidence.append(f'Has instance method: {method.name}')
                confidence += 0.4
                has_instance_method = True
                break

        # Check for private/protected constructor-like methods
        has_init_control = False
        for method in class_sig.methods:
            # Python: __init__ or __new__
            # Java/C#: private constructor (detected by naming)
            if method.name in ['__new__', '__init__', 'constructor']:
                # Check if it has logic (not just pass)
                if method.docstring or len(method.parameters) > 1:
                    evidence.append(f'Controlled initialization: {method.name}')
                    confidence += 0.3
                    has_init_control = True
                    break

        # Check for class-level instance storage
        # This would require checking class attributes (future enhancement)

        if has_instance_method or has_init_control:
            if confidence >= 0.5:
                return PatternInstance(
                    pattern_type=self.pattern_type,
                    category=self.category,
                    confidence=min(confidence, 0.9),
                    location='',
                    class_name=class_sig.name,
                    line_number=class_sig.line_number,
                    evidence=evidence
                )

        # Fallback to surface detection
        return self.detect_surface(class_sig, all_classes)

    def detect_full(
        self,
        class_sig,
        all_classes: List,
        file_content: str
    ) -> Optional[PatternInstance]:
        """
        Full behavioral analysis for Singleton.

        Checks:
        - Instance caching in method body
        - Thread safety (locks, synchronized)
        - Lazy vs eager initialization
        """
        # Start with deep detection
        result = self.detect_deep(class_sig, all_classes)
        if not result:
            return None

        evidence = result.evidence.copy()
        confidence = result.confidence

        # Check for instance caching patterns in code
        caching_patterns = [
            '_instance', '__instance', 'instance',
            'if not', 'if self._instance is None',
            'synchronized', 'Lock()', 'threading'
        ]

        for pattern in caching_patterns:
            if pattern in file_content:
                if pattern not in ' '.join(evidence):
                    evidence.append(f'Instance caching detected: {pattern}')
                    confidence += 0.1

        # Cap confidence at 0.95 (never 100% certain without runtime analysis)
        result.confidence = min(confidence, 0.95)
        result.evidence = evidence

        return result


class FactoryDetector(BasePatternDetector):
    """
    Detect Factory pattern (Factory Method and Abstract Factory).

    Factory defines an interface for creating objects, letting subclasses decide
    which class to instantiate.

    Detection Heuristics:
    - Surface: Class/method name contains 'Factory', 'create', 'make'
    - Deep: Method returns different object types based on parameters
    - Full: Polymorphic object creation with inheritance hierarchy

    Examples:
    - createProduct(type) -> Product
    - ProductFactory with createProductA(), createProductB()
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "Factory"
        self.category = "Creational"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming conventions for Factory"""
        # Check class name
        if 'factory' in class_sig.name.lower():
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.7,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=['Class name contains "Factory"']
            )

        # Check for factory methods
        factory_method_names = ['create', 'make', 'build', 'new', 'get']
        for method in class_sig.methods:
            method_lower = method.name.lower()
            if any(name in method_lower for name in factory_method_names):
                # Check if method returns something (has return type or is not void)
                if method.return_type or 'create' in method_lower:
                    return PatternInstance(
                        pattern_type=self.pattern_type,
                        category=self.category,
                        confidence=0.6,
                        location='',
                        class_name=class_sig.name,
                        method_name=method.name,
                        line_number=method.line_number,
                        evidence=[f'Factory method detected: {method.name}']
                    )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Factory"""
        evidence = []
        confidence = 0.0
        factory_methods = []

        # Look for methods that create objects
        creation_keywords = ['create', 'make', 'build', 'new', 'construct', 'get']

        for method in class_sig.methods:
            method_lower = method.name.lower()

            # Check if method name suggests object creation
            if any(keyword in method_lower for keyword in creation_keywords):
                factory_methods.append(method.name)
                confidence += 0.3

                # Check if it takes parameters (suggests different object types)
                if len(method.parameters) > 1:  # >1 because 'self' counts
                    evidence.append(f'Parameterized factory method: {method.name}')
                    confidence += 0.2
                else:
                    evidence.append(f'Factory method: {method.name}')

        # Check if multiple factory methods exist (Abstract Factory pattern)
        if len(factory_methods) >= 2:
            evidence.append(f'Multiple factory methods: {", ".join(factory_methods[:3])}')
            confidence += 0.2

        # Check for inheritance (factory hierarchy)
        if class_sig.base_classes:
            evidence.append(f'Inherits from: {", ".join(class_sig.base_classes)}')
            confidence += 0.1

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.9),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence,
                related_classes=class_sig.base_classes
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)


class ObserverDetector(BasePatternDetector):
    """
    Detect Observer pattern (Pub/Sub).

    Observer defines one-to-many dependency where multiple objects
    observe and react to state changes.

    Detection Heuristics:
    - Surface: Class/method names with 'Observer', 'Listener', 'Subscribe'
    - Deep: attach/detach + notify methods
    - Full: Collection of observers + iteration pattern

    Examples:
    - addObserver(), removeObserver(), notifyObservers()
    - addEventListener(), removeEventListener(), emit()
    - subscribe(), unsubscribe(), publish()
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "Observer"
        self.category = "Behavioral"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming for Observer pattern"""
        observer_keywords = ['observer', 'listener', 'subscriber', 'watcher']

        # Check class name
        class_lower = class_sig.name.lower()
        if any(keyword in class_lower for keyword in observer_keywords):
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.6,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=[f'Class name suggests Observer: {class_sig.name}']
            )

        # Check method names
        observer_methods = [
            'subscribe', 'unsubscribe', 'publish',
            'addobserver', 'removeobserver', 'notify',
            'addeventlistener', 'removeeventlistener', 'emit',
            'attach', 'detach', 'update'
        ]

        for method in class_sig.methods:
            method_lower = method.name.lower().replace('_', '')
            if any(obs_method in method_lower for obs_method in observer_methods):
                return PatternInstance(
                    pattern_type=self.pattern_type,
                    category=self.category,
                    confidence=0.65,
                    location='',
                    class_name=class_sig.name,
                    method_name=method.name,
                    line_number=method.line_number,
                    evidence=[f'Observer method detected: {method.name}']
                )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Observer"""
        evidence = []
        confidence = 0.0

        # Look for characteristic method triplet: attach/detach/notify
        has_attach = False
        has_detach = False
        has_notify = False

        attach_names = ['attach', 'add', 'subscribe', 'register', 'addeventlistener']
        detach_names = ['detach', 'remove', 'unsubscribe', 'unregister', 'removeeventlistener']
        notify_names = ['notify', 'update', 'emit', 'publish', 'fire', 'trigger']

        for method in class_sig.methods:
            method_lower = method.name.lower().replace('_', '')

            if any(name in method_lower for name in attach_names):
                has_attach = True
                evidence.append(f'Attach method: {method.name}')
                confidence += 0.3

            if any(name in method_lower for name in detach_names):
                has_detach = True
                evidence.append(f'Detach method: {method.name}')
                confidence += 0.3

            if any(name in method_lower for name in notify_names):
                has_notify = True
                evidence.append(f'Notify method: {method.name}')
                confidence += 0.3

        # Strong signal if has all three
        if has_attach and has_detach and has_notify:
            confidence = min(confidence, 0.95)

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.95),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)


class StrategyDetector(BasePatternDetector):
    """
    Detect Strategy pattern.

    Strategy defines a family of algorithms, encapsulates each one,
    and makes them interchangeable.

    Detection Heuristics:
    - Surface: Class/method names with 'Strategy', 'Policy', 'Algorithm'
    - Deep: Interface with single key method + multiple implementations
    - Full: Composition with interchangeable strategy objects

    Examples:
    - SortStrategy with sort() method
    - PaymentStrategy with pay() method
    - CompressionStrategy with compress() method
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "Strategy"
        self.category = "Behavioral"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming for Strategy"""
        strategy_keywords = ['strategy', 'policy', 'algorithm']

        class_lower = class_sig.name.lower()
        if any(keyword in class_lower for keyword in strategy_keywords):
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.7,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=[f'Class name suggests Strategy: {class_sig.name}']
            )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Strategy"""
        evidence = []
        confidence = 0.0

        # Strategy pattern often involves:
        # 1. Base class/interface with key method
        # 2. Multiple subclasses implementing same interface

        # Check if this class is a concrete strategy
        if class_sig.base_classes:
            base_class = class_sig.base_classes[0] if class_sig.base_classes else None

            # Look for siblings (other strategies with same base)
            siblings = [
                cls.name for cls in all_classes
                if cls.base_classes and base_class in cls.base_classes and cls.name != class_sig.name
            ]

            if siblings:
                evidence.append(f'Part of strategy family with: {", ".join(siblings[:3])}')
                confidence += 0.5

            if base_class and ('strategy' in base_class.lower() or 'policy' in base_class.lower()):
                evidence.append(f'Inherits from strategy base: {base_class}')
                confidence += 0.3

        # Check if this is a strategy base class
        # (has subclasses in same file)
        subclasses = [
            cls.name for cls in all_classes
            if class_sig.name in cls.base_classes
        ]

        if len(subclasses) >= 2:
            evidence.append(f'Strategy base with implementations: {", ".join(subclasses[:3])}')
            confidence += 0.6

        # Check for single dominant method (strategy interface)
        if len(class_sig.methods) == 1 or len(class_sig.methods) == 2:
            # Single method or method + __init__
            main_method = [m for m in class_sig.methods if m.name not in ['__init__', '__new__']]
            if main_method:
                evidence.append(f'Strategy interface method: {main_method[0].name}')
                confidence += 0.2

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.9),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence,
                related_classes=class_sig.base_classes + subclasses
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)


class DecoratorDetector(BasePatternDetector):
    """
    Detect Decorator pattern.

    Decorator attaches additional responsibilities to an object dynamically,
    providing flexible alternative to subclassing.

    Detection Heuristics:
    - Surface: Class name contains 'Decorator', 'Wrapper'
    - Deep: Wraps same interface, delegates to wrapped object
    - Full: Composition + delegation + interface matching

    Examples:
    - LoggingDecorator wraps Service
    - CachingDecorator wraps DataFetcher
    - Python @decorator syntax
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "Decorator"
        self.category = "Structural"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming for Decorator"""
        decorator_keywords = ['decorator', 'wrapper', 'proxy']

        class_lower = class_sig.name.lower()
        if any(keyword in class_lower for keyword in decorator_keywords):
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.65,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=[f'Class name suggests Decorator: {class_sig.name}']
            )

        # Check for Python decorator syntax
        for method in class_sig.methods:
            if method.decorators:
                # Has decorators - might be using decorator pattern
                # But this is too common, so low confidence
                return PatternInstance(
                    pattern_type=self.pattern_type,
                    category=self.category,
                    confidence=0.3,
                    location='',
                    class_name=class_sig.name,
                    method_name=method.name,
                    line_number=method.line_number,
                    evidence=[f'Method uses decorators: {method.decorators}']
                )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Decorator"""
        evidence = []
        confidence = 0.0

        # Decorator pattern characteristics:
        # 1. Has same base class as wrapped object
        # 2. Takes wrapped object in constructor
        # 3. Delegates calls to wrapped object

        # Check if shares base class with other classes
        if class_sig.base_classes:
            base_class = class_sig.base_classes[0]

            # Find other classes with same base
            siblings = [
                cls.name for cls in all_classes
                if cls.base_classes and base_class in cls.base_classes and cls.name != class_sig.name
            ]

            if siblings:
                evidence.append(f'Shares interface with: {", ".join(siblings[:2])}')
                confidence += 0.3

        # Check __init__ for composition (takes object parameter)
        init_method = next((m for m in class_sig.methods if m.name == '__init__'), None)
        if init_method:
            # Check if takes object parameter (not just self)
            if len(init_method.parameters) > 1:  # More than just 'self'
                param_names = [p.name for p in init_method.parameters if p.name != 'self']
                if any(name in ['wrapped', 'component', 'inner', 'obj', 'target'] for name in param_names):
                    evidence.append(f'Takes wrapped object in constructor: {param_names}')
                    confidence += 0.4

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.85),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence,
                related_classes=class_sig.base_classes
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)


class BuilderDetector(BasePatternDetector):
    """
    Detect Builder pattern.

    Builder separates construction of complex object from its representation,
    allowing same construction process to create different representations.

    Detection Heuristics:
    - Surface: Class name contains 'Builder'
    - Deep: Fluent interface (methods return self), build()/create() terminal method
    - Full: Multiple configuration methods + final build step

    Examples:
    - QueryBuilder with where(), orderBy(), build()
    - RequestBuilder with setHeader(), setBody(), execute()
    - StringBuilder pattern
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "Builder"
        self.category = "Creational"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming for Builder"""
        if 'builder' in class_sig.name.lower():
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.7,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=[f'Class name contains "Builder": {class_sig.name}']
            )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Builder"""
        evidence = []
        confidence = 0.0

        # Builder characteristics:
        # 1. Multiple setter/configuration methods
        # 2. Terminal build()/create()/execute() method
        # 3. Fluent interface (methods return self/this)

        # Check for build/create terminal method
        terminal_methods = ['build', 'create', 'execute', 'construct', 'make']
        has_terminal = any(
            m.name.lower() in terminal_methods or m.name.lower().startswith('build')
            for m in class_sig.methods
        )

        if has_terminal:
            evidence.append('Has terminal build/create method')
            confidence += 0.4

        # Check for setter methods (with_, set_, add_)
        setter_prefixes = ['with', 'set', 'add', 'configure']
        setter_count = sum(
            1 for m in class_sig.methods
            if any(m.name.lower().startswith(prefix) for prefix in setter_prefixes)
        )

        if setter_count >= 3:
            evidence.append(f'Has {setter_count} configuration methods')
            confidence += 0.4
        elif setter_count >= 1:
            confidence += 0.2

        # Check method count (builders typically have many methods)
        if len(class_sig.methods) >= 5:
            confidence += 0.1

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.9),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)

    def detect_full(
        self,
        class_sig,
        all_classes: List,
        file_content: str
    ) -> Optional[PatternInstance]:
        """Full behavioral analysis for Builder"""
        # Start with deep detection
        pattern = self.detect_deep(class_sig, all_classes)
        if not pattern:
            return None

        evidence = list(pattern.evidence)
        confidence = pattern.confidence

        # Look for fluent interface pattern (return self/this)
        class_content = file_content.lower()
        fluent_indicators = ['return self', 'return this']

        if any(indicator in class_content for indicator in fluent_indicators):
            evidence.append('Uses fluent interface (return self)')
            confidence += 0.1

        # Check for complex object construction (multiple fields)
        if 'self.' in class_content and class_content.count('self.') >= 5:
            evidence.append('Builds complex object with multiple fields')
            confidence += 0.05

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.95),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence
            )

        # Fallback to deep
        return self.detect_deep(class_sig, all_classes)


class AdapterDetector(BasePatternDetector):
    """
    Detect Adapter pattern.

    Adapter converts interface of a class into another interface clients expect,
    allowing incompatible interfaces to work together.

    Detection Heuristics:
    - Surface: Class name contains 'Adapter', 'Wrapper'
    - Deep: Wraps external/incompatible class, translates method calls
    - Full: Composition + delegation with interface translation

    Examples:
    - DatabaseAdapter wraps external DB library
    - ApiAdapter translates REST to internal interface
    - FileSystemAdapter wraps OS file operations
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "Adapter"
        self.category = "Structural"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming for Adapter"""
        adapter_keywords = ['adapter', 'wrapper', 'bridge']

        class_lower = class_sig.name.lower()
        if any(keyword in class_lower for keyword in adapter_keywords):
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.7,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=[f'Class name suggests Adapter: {class_sig.name}']
            )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Adapter"""
        evidence = []
        confidence = 0.0

        # Adapter characteristics:
        # 1. Takes adaptee in constructor
        # 2. Implements target interface
        # 3. Delegates to adaptee with translation

        # Check __init__ for composition (takes adaptee)
        init_method = next((m for m in class_sig.methods if m.name == '__init__'), None)
        if init_method:
            if len(init_method.parameters) > 1:  # More than just 'self'
                param_names = [p.name for p in init_method.parameters if p.name != 'self']
                adaptee_names = ['adaptee', 'wrapped', 'client', 'service', 'api', 'source']
                if any(name in param_names for name in adaptee_names):
                    evidence.append(f'Takes adaptee in constructor: {param_names}')
                    confidence += 0.4

        # Check if implements interface (has base class)
        if class_sig.base_classes:
            evidence.append(f'Implements interface: {class_sig.base_classes[0]}')
            confidence += 0.3

        # Check for delegation methods (methods that likely call adaptee)
        if len(class_sig.methods) >= 3:  # Multiple interface methods
            evidence.append(f'Has {len(class_sig.methods)} interface methods')
            confidence += 0.2

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.85),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)


class CommandDetector(BasePatternDetector):
    """
    Detect Command pattern.

    Command encapsulates a request as an object, allowing parameterization
    of clients with different requests, queuing, logging, and undo operations.

    Detection Heuristics:
    - Surface: Class name contains 'Command', 'Action', 'Task'
    - Deep: Has execute()/run() method, encapsulates action
    - Full: Receiver composition + undo support

    Examples:
    - SaveCommand with execute() method
    - UndoableCommand with undo() and redo()
    - TaskCommand in task queue
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "Command"
        self.category = "Behavioral"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming for Command"""
        command_keywords = ['command', 'action', 'task', 'operation']

        class_lower = class_sig.name.lower()
        if any(keyword in class_lower for keyword in command_keywords):
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.65,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=[f'Class name suggests Command: {class_sig.name}']
            )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Command"""
        evidence = []
        confidence = 0.0

        # Command characteristics:
        # 1. Has execute()/run()/call() method
        # 2. May have undo()/redo() methods
        # 3. Encapsulates receiver and parameters

        # Check for execute/run method
        execute_methods = ['execute', 'run', 'call', 'do', 'perform', '__call__']
        has_execute = any(
            m.name.lower() in execute_methods
            for m in class_sig.methods
        )

        if has_execute:
            method_name = next(m.name for m in class_sig.methods if m.name.lower() in execute_methods)
            evidence.append(f'Has execute method: {method_name}()')
            confidence += 0.5

        # Check for undo/redo support
        undo_methods = ['undo', 'rollback', 'revert', 'redo']
        has_undo = any(
            m.name.lower() in undo_methods
            for m in class_sig.methods
        )

        if has_undo:
            evidence.append('Supports undo/redo operations')
            confidence += 0.3

        # Check for receiver (takes object in __init__)
        init_method = next((m for m in class_sig.methods if m.name == '__init__'), None)
        if init_method and len(init_method.parameters) > 1:
            evidence.append('Encapsulates receiver/parameters')
            confidence += 0.2

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.9),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)


class TemplateMethodDetector(BasePatternDetector):
    """
    Detect Template Method pattern.

    Template Method defines skeleton of algorithm in base class,
    letting subclasses override specific steps without changing structure.

    Detection Heuristics:
    - Surface: Abstract/Base class with template-like names
    - Deep: Abstract base with hook methods, concrete subclasses override
    - Full: Template method calls abstract/hook methods

    Examples:
    - AbstractProcessor with process() calling abstract steps
    - BaseParser with parse() template method
    - Framework base classes with lifecycle hooks
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "TemplateMethod"
        self.category = "Behavioral"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming for Template Method"""
        template_keywords = ['abstract', 'base', 'template']

        class_lower = class_sig.name.lower()
        if any(keyword in class_lower for keyword in template_keywords):
            # Check if has subclasses
            subclasses = [
                cls.name for cls in all_classes
                if class_sig.name in cls.base_classes
            ]

            if subclasses:
                return PatternInstance(
                    pattern_type=self.pattern_type,
                    category=self.category,
                    confidence=0.6,
                    location='',
                    class_name=class_sig.name,
                    line_number=class_sig.line_number,
                    evidence=[f'Abstract base with subclasses: {", ".join(subclasses[:2])}'],
                    related_classes=subclasses
                )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Template Method"""
        evidence = []
        confidence = 0.0

        # Template Method characteristics:
        # 1. Has subclasses (is base class)
        # 2. Has methods that look like hooks (prepare, validate, cleanup, etc.)
        # 3. Has template method that orchestrates

        # Check for subclasses
        subclasses = [
            cls.name for cls in all_classes
            if class_sig.name in cls.base_classes
        ]

        if len(subclasses) >= 1:
            evidence.append(f'Base class with {len(subclasses)} implementations')
            confidence += 0.4

        # Check for hook-like method names
        hook_keywords = ['prepare', 'initialize', 'validate', 'process', 'finalize',
                        'setup', 'teardown', 'before', 'after', 'pre', 'post', 'hook']

        hook_methods = [
            m.name for m in class_sig.methods
            if any(keyword in m.name.lower() for keyword in hook_keywords)
        ]

        if len(hook_methods) >= 2:
            evidence.append(f'Has hook methods: {", ".join(hook_methods[:3])}')
            confidence += 0.3

        # Check for abstract methods (no implementation or pass/raise)
        abstract_methods = [
            m.name for m in class_sig.methods
            if m.name.startswith('_') or 'abstract' in m.name.lower()
        ]

        if abstract_methods:
            evidence.append(f'Has abstract methods: {", ".join(abstract_methods[:2])}')
            confidence += 0.2

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.85),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence,
                related_classes=subclasses
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)


class ChainOfResponsibilityDetector(BasePatternDetector):
    """
    Detect Chain of Responsibility pattern.

    Chain of Responsibility passes request along chain of handlers until
    one handles it, avoiding coupling sender to receiver.

    Detection Heuristics:
    - Surface: Class name contains 'Handler', 'Chain', 'Middleware'
    - Deep: Has next/successor reference, handle() method
    - Full: Chain traversal logic, request passing

    Examples:
    - LogHandler with next handler
    - AuthMiddleware chain
    - EventHandler chain
    """

    def __init__(self, depth: str = 'deep'):
        super().__init__(depth)
        self.pattern_type = "ChainOfResponsibility"
        self.category = "Behavioral"

    def detect_surface(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Check naming for Chain of Responsibility"""
        chain_keywords = ['handler', 'chain', 'middleware', 'filter', 'processor']

        class_lower = class_sig.name.lower()
        if any(keyword in class_lower for keyword in chain_keywords):
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=0.6,
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=[f'Class name suggests handler chain: {class_sig.name}']
            )

        return None

    def detect_deep(
        self,
        class_sig,
        all_classes: List
    ) -> Optional[PatternInstance]:
        """Structural analysis for Chain of Responsibility"""
        evidence = []
        confidence = 0.0

        # Chain of Responsibility characteristics:
        # 1. Has handle()/process() method
        # 2. Has next/successor reference
        # 3. May have set_next() method

        # Check for handle/process method
        handle_methods = ['handle', 'process', 'execute', 'filter', 'middleware']
        has_handle = any(
            m.name.lower() in handle_methods or m.name.lower().startswith('handle')
            for m in class_sig.methods
        )

        if has_handle:
            evidence.append('Has handle/process method')
            confidence += 0.4

        # Check for next/successor methods or parameters
        init_method = next((m for m in class_sig.methods if m.name == '__init__'), None)
        has_next_ref = False

        if init_method:
            param_names = [p.name for p in init_method.parameters if p.name != 'self']
            next_names = ['next', 'successor', 'next_handler', 'next_middleware']

            if any(name in param_names for name in next_names):
                evidence.append('Takes next handler in chain')
                confidence += 0.3
                has_next_ref = True

        # Check for set_next() method
        has_set_next = any(
            'next' in m.name.lower() and ('set' in m.name.lower() or 'add' in m.name.lower())
            for m in class_sig.methods
        )

        if has_set_next:
            evidence.append('Has set_next() method')
            confidence += 0.3
            has_next_ref = True

        # Check if part of handler family (shares base class)
        if class_sig.base_classes:
            base_class = class_sig.base_classes[0]
            siblings = [
                cls.name for cls in all_classes
                if cls.base_classes and base_class in cls.base_classes and cls.name != class_sig.name
            ]

            if siblings and has_next_ref:
                evidence.append(f'Part of handler chain with: {", ".join(siblings[:2])}')
                confidence += 0.2

        if confidence >= 0.5:
            return PatternInstance(
                pattern_type=self.pattern_type,
                category=self.category,
                confidence=min(confidence, 0.9),
                location='',
                class_name=class_sig.name,
                line_number=class_sig.line_number,
                evidence=evidence
            )

        # Fallback to surface
        return self.detect_surface(class_sig, all_classes)


class LanguageAdapter:
    """
    Language-specific pattern detection adaptations.

    Adjusts pattern confidence based on language idioms and conventions.
    Different languages have different ways of implementing patterns.
    """

    @staticmethod
    def adapt_for_language(
        pattern: PatternInstance,
        language: str
    ) -> PatternInstance:
        """
        Adjust confidence based on language-specific idioms.

        Args:
            pattern: Detected pattern instance
            language: Programming language

        Returns:
            Adjusted pattern instance with language-specific confidence
        """
        if not pattern:
            return pattern

        evidence_str = ' '.join(pattern.evidence).lower()

        # Python-specific adaptations
        if language == 'Python':
            # Decorator pattern: Python has native @ syntax
            if pattern.pattern_type == 'Decorator':
                if '@' in ' '.join(pattern.evidence):
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)
                    pattern.evidence.append('Python @decorator syntax detected')

            # Singleton: __new__ method is Python idiom
            elif pattern.pattern_type == 'Singleton':
                if '__new__' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)

            # Strategy: Duck typing common in Python
            elif pattern.pattern_type == 'Strategy':
                if 'duck typing' in evidence_str or 'protocol' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.05, 1.0)

        # JavaScript/TypeScript adaptations
        elif language in ['JavaScript', 'TypeScript']:
            # Singleton: Module pattern is common
            if pattern.pattern_type == 'Singleton':
                if 'module' in evidence_str or 'export default' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)
                    pattern.evidence.append('JavaScript module pattern')

            # Factory: Factory functions are idiomatic
            elif pattern.pattern_type == 'Factory':
                if 'create' in evidence_str or 'make' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.05, 1.0)

            # Observer: Event emitters are built-in
            elif pattern.pattern_type == 'Observer':
                if 'eventemitter' in evidence_str or 'event' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)
                    pattern.evidence.append('EventEmitter pattern detected')

        # Java/C# adaptations (interface-heavy languages)
        elif language in ['Java', 'C#']:
            # All patterns: Interfaces are explicit
            if 'interface' in evidence_str:
                pattern.confidence = min(pattern.confidence + 0.05, 1.0)

            # Factory: Abstract Factory common
            if pattern.pattern_type == 'Factory':
                if 'abstract' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)
                    pattern.evidence.append('Abstract Factory pattern')

            # Template Method: Abstract classes common
            elif pattern.pattern_type == 'TemplateMethod':
                if 'abstract' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)

        # Go adaptations
        elif language == 'Go':
            # Singleton: sync.Once is idiomatic
            if pattern.pattern_type == 'Singleton':
                if 'sync.once' in evidence_str or 'once.do' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.15, 1.0)
                    pattern.evidence.append('Go sync.Once idiom')

            # Strategy: Interfaces are implicit
            elif pattern.pattern_type == 'Strategy':
                if 'interface{}' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.05, 1.0)

        # Rust adaptations
        elif language == 'Rust':
            # Singleton: Lazy static is common
            if pattern.pattern_type == 'Singleton':
                if 'lazy_static' in evidence_str or 'oncecell' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.15, 1.0)
                    pattern.evidence.append('Rust lazy_static/OnceCell')

            # Builder: Derive builder is idiomatic
            elif pattern.pattern_type == 'Builder':
                if 'derive' in evidence_str and 'builder' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)

            # Adapter: Trait adapters are common
            elif pattern.pattern_type == 'Adapter':
                if 'trait' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)

        # C++ adaptations
        elif language == 'C++':
            # Singleton: Meyer's Singleton is idiomatic
            if pattern.pattern_type == 'Singleton':
                if 'static' in evidence_str and 'local' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)
                    pattern.evidence.append("Meyer's Singleton (static local)")

            # Factory: Template-based factories
            elif pattern.pattern_type == 'Factory':
                if 'template' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.05, 1.0)

        # Ruby adaptations
        elif language == 'Ruby':
            # Singleton: Ruby has Singleton module
            if pattern.pattern_type == 'Singleton':
                if 'include singleton' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.2, 1.0)
                    pattern.evidence.append('Ruby Singleton module')

            # Builder: Method chaining is idiomatic
            elif pattern.pattern_type == 'Builder':
                if 'method chaining' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.05, 1.0)

        # PHP adaptations
        elif language == 'PHP':
            # Singleton: Private constructor is common
            if pattern.pattern_type == 'Singleton':
                if 'private' in evidence_str and '__construct' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)

            # Factory: Static factory methods
            elif pattern.pattern_type == 'Factory':
                if 'static' in evidence_str:
                    pattern.confidence = min(pattern.confidence + 0.05, 1.0)

        return pattern


def main():
    """
    CLI entry point for pattern detection.

    Usage:
        skill-seekers-patterns --file src/database.py
        skill-seekers-patterns --directory src/ --output patterns/
        skill-seekers-patterns --file app.py --depth full --json
    """
    import argparse
    import sys
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description='Detect design patterns in source code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file
  skill-seekers-patterns --file src/database.py

  # Analyze directory
  skill-seekers-patterns --directory src/ --output patterns/

  # Full analysis with JSON output
  skill-seekers-patterns --file app.py --depth full --json

  # Multiple files
  skill-seekers-patterns --file src/db.py --file src/api.py

Supported Languages:
  Python, JavaScript, TypeScript, C++, C, C#, Go, Rust, Java, Ruby, PHP
"""
    )

    parser.add_argument(
        '--file',
        action='append',
        help='Source file to analyze (can be specified multiple times)'
    )
    parser.add_argument(
        '--directory',
        help='Directory to analyze (analyzes all source files)'
    )
    parser.add_argument(
        '--output',
        help='Output directory for results (default: current directory)'
    )
    parser.add_argument(
        '--depth',
        choices=['surface', 'deep', 'full'],
        default='deep',
        help='Detection depth: surface (fast), deep (default), full (thorough)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON format instead of human-readable'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.file and not args.directory:
        parser.error("Must specify either --file or --directory")

    # Create recognizer
    recognizer = PatternRecognizer(depth=args.depth)

    # Collect files to analyze
    files_to_analyze = []

    if args.file:
        for file_path in args.file:
            path = Path(file_path)
            if not path.exists():
                print(f"Error: File not found: {file_path}", file=sys.stderr)
                return 1
            files_to_analyze.append(path)

    if args.directory:
        from skill_seekers.cli.codebase_scraper import walk_directory, detect_language
        directory = Path(args.directory)
        if not directory.exists():
            print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
            return 1

        # Walk directory for source files
        files_to_analyze.extend(walk_directory(directory))

    if not files_to_analyze:
        print("No source files found to analyze", file=sys.stderr)
        return 1

    # Analyze files
    all_reports = []
    total_patterns = 0

    for file_path in files_to_analyze:
        try:
            from skill_seekers.cli.codebase_scraper import detect_language

            content = file_path.read_text(encoding='utf-8', errors='ignore')
            language = detect_language(file_path)

            if language == 'Unknown':
                if args.verbose:
                    print(f"Skipping {file_path}: Unknown language")
                continue

            report = recognizer.analyze_file(str(file_path), content, language)

            if report.patterns:
                all_reports.append(report)
                total_patterns += len(report.patterns)

                if not args.json and args.verbose:
                    print(f"\n{file_path}:")
                    for pattern in report.patterns:
                        print(f"  [{pattern.pattern_type}] {pattern.class_name} (confidence: {pattern.confidence:.2f})")

        except Exception as e:
            if args.verbose:
                print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
            continue

    # Output results
    if args.json:
        # JSON output
        output_data = {
            'total_files_analyzed': len(files_to_analyze),
            'files_with_patterns': len(all_reports),
            'total_patterns_detected': total_patterns,
            'reports': [report.to_dict() for report in all_reports]
        }

        if args.output:
            output_path = Path(args.output) / 'detected_patterns.json'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            print(f"Results saved to: {output_path}")
        else:
            print(json.dumps(output_data, indent=2))

    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print(f"PATTERN DETECTION RESULTS")
        print(f"{'='*60}")
        print(f"Files analyzed: {len(files_to_analyze)}")
        print(f"Files with patterns: {len(all_reports)}")
        print(f"Total patterns detected: {total_patterns}")
        print(f"{'='*60}\n")

        # Pattern summary by type
        pattern_counts = {}
        for report in all_reports:
            for pattern in report.patterns:
                pattern_counts[pattern.pattern_type] = pattern_counts.get(pattern.pattern_type, 0) + 1

        if pattern_counts:
            print("Pattern Summary:")
            for pattern_type, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {pattern_type}: {count}")
            print()

        # Detailed results
        if all_reports:
            print("Detected Patterns:\n")
            for report in all_reports:
                print(f"{report.file_path}:")
                for pattern in report.patterns:
                    print(f"  • {pattern.pattern_type} - {pattern.class_name}")
                    print(f"    Confidence: {pattern.confidence:.2f}")
                    print(f"    Category: {pattern.category}")
                    if pattern.evidence:
                        print(f"    Evidence: {pattern.evidence[0]}")
                    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
