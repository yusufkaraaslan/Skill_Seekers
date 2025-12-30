#!/usr/bin/env python3
"""
Test Suite for Swift Language Detection

Tests confidence-based Swift detection including:
- Pure Swift syntax (structs, protocols, extensions, optionals, generics)
- iOS/UIKit patterns (UIViewController, IBOutlet, lifecycle methods)
- macOS/AppKit patterns (NSViewController, NSWindow, AppKit classes)
- SwiftUI patterns (@State, @Binding, View protocol, modifiers)
- Combine framework patterns
- Swift Concurrency (async/await, actors)
- Foundation Models (iOS/macOS 26+: @Generable, LanguageModelSession, SystemLanguageModel)

Run with: pytest tests/test_swift_detection.py -v
"""

import pytest
from bs4 import BeautifulSoup
from skill_seekers.cli.language_detector import LanguageDetector


class TestSwiftCSSClassDetection:
    """Test Swift detection from CSS classes"""

    def test_language_swift_class(self):
        """Test language-swift CSS class"""
        detector = LanguageDetector()
        classes = ['language-swift', 'highlight']
        assert detector.extract_language_from_classes(classes) == 'swift'

    def test_lang_swift_class(self):
        """Test lang-swift CSS class"""
        detector = LanguageDetector()
        classes = ['lang-swift', 'code']
        assert detector.extract_language_from_classes(classes) == 'swift'

    def test_bare_swift_class(self):
        """Test bare 'swift' class name"""
        detector = LanguageDetector()
        classes = ['swift', 'highlight']
        assert detector.extract_language_from_classes(classes) == 'swift'

    def test_detect_from_html_swift_class(self):
        """Test HTML element with Swift CSS class"""
        detector = LanguageDetector()
        html = '<code class="language-swift">let x = 5</code>'
        soup = BeautifulSoup(html, 'html.parser')
        elem = soup.find('code')

        lang, confidence = detector.detect_from_html(elem, 'let x = 5')
        assert lang == 'swift'
        assert confidence == 1.0  # CSS class = high confidence


class TestPureSwiftDetection:
    """Test pure Swift syntax detection"""

    def test_func_with_return_type(self):
        """Test Swift function with return type"""
        detector = LanguageDetector()
        code = """
        func calculateSum(a: Int, b: Int) -> Int {
            return a + b
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.5

    def test_struct_declaration(self):
        """Test Swift struct declaration"""
        detector = LanguageDetector()
        code = """
        struct Person: Codable {
            let name: String
            var age: Int
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.6

    def test_protocol_declaration(self):
        """Test Swift protocol declaration"""
        detector = LanguageDetector()
        code = """
        protocol DataProvider {
            associatedtype DataType
            func fetchData() -> DataType
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_extension_declaration(self):
        """Test Swift extension"""
        detector = LanguageDetector()
        code = """
        extension String {
            func trimmed() -> String {
                return self.trimmingCharacters(in: .whitespaces)
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_guard_let_unwrapping(self):
        """Test Swift guard let optional unwrapping"""
        detector = LanguageDetector()
        code = """
        func process(value: String?) {
            guard let unwrapped = value else {
                return
            }
            print(unwrapped)
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_if_let_unwrapping(self):
        """Test Swift if let optional unwrapping"""
        detector = LanguageDetector()
        code = """
        if let name = optionalName {
            print("Hello, \\(name)")
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.5

    def test_closure_syntax(self):
        """Test Swift closure syntax"""
        detector = LanguageDetector()
        code = """
        let numbers = [1, 2, 3, 4, 5]
        let doubled = numbers.map { $0 * 2 }
        let filtered = numbers.filter { (num) in num > 2 }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.5

    def test_error_handling(self):
        """Test Swift error handling (try/catch/throws)"""
        detector = LanguageDetector()
        code = """
        func loadData() throws -> Data {
            guard let url = URL(string: "https://api.example.com") else {
                throw NetworkError.invalidURL
            }
            return try Data(contentsOf: url)
        }

        do {
            let data = try loadData()
        } catch {
            print(error)
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_async_await(self):
        """Test Swift async/await (Swift 5.5+)"""
        detector = LanguageDetector()
        code = """
        func fetchUser() async throws -> User {
            let url = URL(string: "https://api.example.com/user")!
            let (data, _) = try await URLSession.shared.data(from: url)
            return try JSONDecoder().decode(User.self, from: data)
        }

        Task {
            let user = try await fetchUser()
            print(user.name)
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_actor_declaration(self):
        """Test Swift actor (Swift 5.5+)"""
        detector = LanguageDetector()
        code = """
        actor BankAccount {
            private var balance: Double = 0

            func deposit(_ amount: Double) {
                balance += amount
            }

            func getBalance() -> Double {
                return balance
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.6

    def test_generics_with_constraints(self):
        """Test Swift generics with constraints"""
        detector = LanguageDetector()
        code = """
        func findItem<T: Equatable>(in array: [T], matching item: T) -> Int? {
            for (index, element) in array.enumerated() where element == item {
                return index
            }
            return nil
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.6

    def test_enum_with_associated_values(self):
        """Test Swift enum with associated values"""
        detector = LanguageDetector()
        code = """
        enum Result<Success, Failure: Error> {
            case success(Success)
            case failure(Failure)
        }

        enum NetworkError: Error {
            case invalidURL
            case noConnection
            case timeout(seconds: Int)
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.4  # Enums without strong Swift keywords have lower confidence

    def test_opaque_types(self):
        """Test Swift opaque types (some keyword)"""
        detector = LanguageDetector()
        code = """
        func makeShape() -> some Shape {
            return Circle()
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.5


class TestUIKitDetection:
    """Test iOS/UIKit pattern detection"""

    def test_viewcontroller_lifecycle(self):
        """Test UIViewController lifecycle methods"""
        detector = LanguageDetector()
        code = """
        import UIKit

        class HomeViewController: UIViewController {
            override func viewDidLoad() {
                super.viewDidLoad()
                setupUI()
            }

            override func viewWillAppear(_ animated: Bool) {
                super.viewWillAppear(animated)
            }

            override func viewDidAppear(_ animated: Bool) {
                super.viewDidAppear(animated)
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_iboutlet_ibaction(self):
        """Test @IBOutlet and @IBAction"""
        detector = LanguageDetector()
        code = """
        class LoginViewController: UIViewController {
            @IBOutlet weak var usernameTextField: UITextField!
            @IBOutlet weak var passwordTextField: UITextField!
            @IBOutlet weak var loginButton: UIButton!

            @IBAction func loginTapped(_ sender: UIButton) {
                authenticate()
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_tableview_delegate(self):
        """Test UITableView delegate/datasource"""
        detector = LanguageDetector()
        code = """
        extension ViewController: UITableViewDelegate, UITableViewDataSource {
            func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
                return items.count
            }

            func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
                let cell = tableView.dequeueReusableCell(withIdentifier: "Cell", for: indexPath)
                cell.textLabel?.text = items[indexPath.row]
                return cell
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_auto_layout_constraints(self):
        """Test Auto Layout constraint code"""
        detector = LanguageDetector()
        code = """
        func setupConstraints() {
            button.translatesAutoresizingMaskIntoConstraints = false
            NSLayoutConstraint.activate([
                button.centerXAnchor.constraint(equalTo: view.centerXAnchor),
                button.centerYAnchor.constraint(equalTo: view.centerYAnchor),
                button.widthAnchor.constraint(equalToConstant: 200),
                button.heightAnchor.constraint(equalToConstant: 50)
            ])
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_dispatch_queue(self):
        """Test DispatchQueue usage"""
        detector = LanguageDetector()
        code = """
        func fetchData() {
            DispatchQueue.global(qos: .background).async {
                let data = self.loadFromNetwork()

                DispatchQueue.main.async { [weak self] in
                    self?.updateUI(with: data)
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_codable_json(self):
        """Test Codable JSON encoding/decoding"""
        detector = LanguageDetector()
        code = """
        struct User: Codable {
            let id: Int
            let name: String
            let email: String

            enum CodingKeys: String, CodingKey {
                case id
                case name
                case email = "email_address"
            }
        }

        let decoder = JSONDecoder()
        let user = try decoder.decode(User.self, from: jsonData)
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9


class TestAppKitDetection:
    """Test macOS/AppKit pattern detection"""

    def test_nsviewcontroller_lifecycle(self):
        """Test NSViewController lifecycle methods"""
        detector = LanguageDetector()
        code = """
        import AppKit

        class MainViewController: NSViewController {
            override func viewDidLoad() {
                super.viewDidLoad()
                setupUI()
            }

            override func viewWillAppear() {
                super.viewWillAppear()
            }

            override func viewDidAppear() {
                super.viewDidAppear()
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_nswindow_controller(self):
        """Test NSWindowController"""
        detector = LanguageDetector()
        code = """
        import Cocoa

        class PreferencesWindowController: NSWindowController {
            override func windowDidLoad() {
                super.windowDidLoad()
                window?.title = "Preferences"
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_nstableview_delegate(self):
        """Test NSTableView delegate/datasource"""
        detector = LanguageDetector()
        code = """
        extension ViewController: NSTableViewDelegate, NSTableViewDataSource {
            func numberOfRows(in tableView: NSTableView) -> Int {
                return items.count
            }

            func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
                let cell = tableView.makeView(withIdentifier: NSUserInterfaceItemIdentifier("Cell"), owner: nil) as? NSTableCellView
                cell?.textField?.stringValue = items[row]
                return cell
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_nsapplication_delegate(self):
        """Test NSApplicationDelegate"""
        detector = LanguageDetector()
        code = """
        import Cocoa

        @main
        class AppDelegate: NSObject, NSApplicationDelegate {
            func applicationDidFinishLaunching(_ notification: Notification) {
                // Setup code
            }

            func applicationWillTerminate(_ notification: Notification) {
                // Cleanup code
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_nsmenu_toolbar(self):
        """Test NSMenu and NSToolbar"""
        detector = LanguageDetector()
        code = """
        func setupMenu() {
            let menu = NSMenu(title: "File")
            let menuItem = NSMenuItem(title: "New", action: #selector(newDocument), keyEquivalent: "n")
            menu.addItem(menuItem)

            let toolbar = NSToolbar(identifier: "MainToolbar")
            toolbar.delegate = self
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_nspanel_dialogs(self):
        """Test NSOpenPanel and NSSavePanel"""
        detector = LanguageDetector()
        code = """
        func showOpenPanel() {
            let panel = NSOpenPanel()
            panel.allowsMultipleSelection = true
            panel.canChooseDirectories = true

            if panel.runModal() == .OK {
                for url in panel.urls {
                    processFile(at: url)
                }
            }
        }

        func showSavePanel() {
            let panel = NSSavePanel()
            panel.allowedContentTypes = [.png]

            if panel.runModal() == .OK {
                saveFile(to: panel.url!)
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_nsstatusbar_menubar_extra(self):
        """Test NSStatusBar for menu bar apps"""
        detector = LanguageDetector()
        code = """
        class StatusBarController {
            private var statusItem: NSStatusItem?

            func setup() {
                statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
                statusItem?.button?.image = NSImage(systemSymbolName: "star", accessibilityDescription: nil)

                let menu = NSMenu()
                menu.addItem(NSMenuItem(title: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
                statusItem?.menu = menu
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9


class TestSwiftUIDetection:
    """Test SwiftUI pattern detection"""

    def test_basic_swiftui_view(self):
        """Test basic SwiftUI View"""
        detector = LanguageDetector()
        code = """
        import SwiftUI

        struct ContentView: View {
            var body: some View {
                Text("Hello, World!")
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_state_binding(self):
        """Test @State and @Binding"""
        detector = LanguageDetector()
        code = """
        struct CounterView: View {
            @State private var count = 0

            var body: some View {
                VStack {
                    Text("Count: \\(count)")
                    Button("Increment") {
                        count += 1
                    }
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_observable_object(self):
        """Test @Published and @ObservedObject"""
        detector = LanguageDetector()
        code = """
        class UserViewModel: ObservableObject {
            @Published var username = ""
            @Published var isLoggedIn = false
        }

        struct ProfileView: View {
            @ObservedObject var viewModel: UserViewModel

            var body: some View {
                Text(viewModel.username)
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_environment_object(self):
        """Test @EnvironmentObject and @Environment"""
        detector = LanguageDetector()
        code = """
        struct SettingsView: View {
            @EnvironmentObject var settings: AppSettings
            @Environment(\\.colorScheme) var colorScheme

            var body: some View {
                Form {
                    Toggle("Dark Mode", isOn: $settings.darkModeEnabled)
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_swiftui_stacks(self):
        """Test VStack, HStack, ZStack"""
        detector = LanguageDetector()
        code = """
        struct LayoutView: View {
            var body: some View {
                VStack {
                    HStack {
                        Text("Left")
                        Spacer()
                        Text("Right")
                    }
                    ZStack {
                        Color.blue
                        Text("Overlay")
                    }
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_swiftui_navigation(self):
        """Test NavigationView/NavigationStack and NavigationLink"""
        detector = LanguageDetector()
        code = """
        struct MainView: View {
            var body: some View {
                NavigationStack {
                    List {
                        NavigationLink("Detail", destination: DetailView())
                    }
                    .navigationTitle("Home")
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_swiftui_modifiers(self):
        """Test SwiftUI view modifiers"""
        detector = LanguageDetector()
        code = """
        Text("Hello")
            .font(.title)
            .foregroundColor(.blue)
            .padding()
            .background(Color.gray.opacity(0.2))
            .cornerRadius(10)
            .shadow(radius: 5)
            .onAppear {
                print("View appeared")
            }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_swiftui_list_foreach(self):
        """Test List and ForEach"""
        detector = LanguageDetector()
        code = """
        struct ItemListView: View {
            let items = ["Apple", "Banana", "Cherry"]

            var body: some View {
                List {
                    ForEach(items, id: \\.self) { item in
                        Text(item)
                    }
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_swiftui_sheet_alert(self):
        """Test .sheet and .alert modifiers"""
        detector = LanguageDetector()
        code = """
        struct ContentView: View {
            @State private var showSheet = false
            @State private var showAlert = false

            var body: some View {
                Button("Show Sheet") { showSheet = true }
                    .sheet(isPresented: $showSheet) {
                        Text("Sheet Content")
                    }
                    .alert("Alert Title", isPresented: $showAlert) {
                        Button("OK", role: .cancel) { }
                    }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_swiftui_macos_window_group(self):
        """Test macOS SwiftUI WindowGroup and Scene"""
        detector = LanguageDetector()
        code = """
        import SwiftUI

        @main
        struct MyMacApp: App {
            var body: some Scene {
                WindowGroup {
                    ContentView()
                }
                .windowStyle(.hiddenTitleBar)

                Settings {
                    SettingsView()
                }

                MenuBarExtra("Status", systemImage: "star") {
                    MenuBarView()
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.95

    def test_swiftui_navigation_split_view(self):
        """Test NavigationSplitView (macOS/iPad)"""
        detector = LanguageDetector()
        code = """
        struct SidebarView: View {
            @State private var selection: Item?

            var body: some View {
                NavigationSplitView {
                    List(items, selection: $selection) { item in
                        NavigationLink(value: item) {
                            Text(item.title)
                        }
                    }
                    .navigationTitle("Sidebar")
                } detail: {
                    if let selection {
                        DetailView(item: selection)
                    } else {
                        Text("Select an item")
                    }
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_swift_observation(self):
        """Test Swift 5.9 @Observable macro"""
        detector = LanguageDetector()
        code = """
        import SwiftUI

        @Observable
        class ViewModel {
            var items: [Item] = []
            var isLoading = false
        }

        struct ContentView: View {
            @Bindable var viewModel: ViewModel

            var body: some View {
                List(viewModel.items) { item in
                    Text(item.name)
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9


class TestCombineDetection:
    """Test Combine framework patterns"""

    def test_combine_publisher_subscriber(self):
        """Test Combine Publisher and Subscriber"""
        detector = LanguageDetector()
        code = """
        import Combine

        class DataService {
            private var cancellables = Set<AnyCancellable>()

            func fetchData() -> AnyPublisher<[Item], Error> {
                URLSession.shared.dataTaskPublisher(for: url)
                    .map(\\.data)
                    .decode(type: [Item].self, decoder: JSONDecoder())
                    .receive(on: RunLoop.main)
                    .eraseToAnyPublisher()
            }

            func subscribe() {
                fetchData()
                    .sink { completion in
                        print(completion)
                    } receiveValue: { items in
                        self.items = items
                    }
                    .store(in: &cancellables)
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9

    def test_combine_subjects(self):
        """Test PassthroughSubject and CurrentValueSubject"""
        detector = LanguageDetector()
        code = """
        import Combine

        class EventBus {
            let messageSubject = PassthroughSubject<String, Never>()
            let counterSubject = CurrentValueSubject<Int, Never>(0)

            func sendMessage(_ message: String) {
                messageSubject.send(message)
            }

            func incrementCounter() {
                counterSubject.value += 1
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.9


class TestSwiftConfidenceScoring:
    """Test confidence scoring accuracy"""

    def test_minimal_swift_code(self):
        """Test minimal Swift code (edge case)"""
        detector = LanguageDetector()
        # Note: "let x: Int = 5" is ambiguous with TypeScript
        # Use guard let which is Swift-unique and gets high confidence
        code = "guard let value = optional else { return }"
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.5  # guard let is very Swift-specific

    def test_high_confidence_full_app(self):
        """Test complete SwiftUI app (high confidence expected)"""
        detector = LanguageDetector()
        code = """
        import SwiftUI

        @main
        struct MyApp: App {
            @StateObject private var viewModel = AppViewModel()

            var body: some Scene {
                WindowGroup {
                    ContentView()
                        .environmentObject(viewModel)
                }
            }
        }

        struct ContentView: View {
            @EnvironmentObject var viewModel: AppViewModel
            @State private var searchText = ""

            var body: some View {
                NavigationStack {
                    List {
                        ForEach(viewModel.filteredItems) { item in
                            NavigationLink(destination: DetailView(item: item)) {
                                ItemRow(item: item)
                            }
                        }
                    }
                    .navigationTitle("Items")
                    .searchable(text: $searchText)
                    .refreshable {
                        await viewModel.refresh()
                    }
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.95

    def test_swift_vs_similar_languages(self):
        """
        Test Swift doesn't false-positive for similar syntax in other languages.

        Critical for avoiding misclassification of:
        - Go: 'func', ':=' short declaration
        - Rust: 'fn', 'let mut', struct
        - TypeScript: 'let', 'const', type annotations with ':'

        These languages share keywords or syntax patterns with Swift,
        so detection must use unique Swift patterns (guard let, @State, etc.)
        """
        detector = LanguageDetector()

        # Go code (also uses 'func')
        go_code = """
        package main

        func main() {
            message := "Hello"
            fmt.Println(message)
        }
        """
        lang, _ = detector.detect_from_code(go_code)
        assert lang == 'go', f"Expected 'go', got '{lang}'"

        # Rust code (also uses 'struct', 'fn')
        rust_code = """
        fn main() {
            let mut x = 5;
            println!("Value: {}", x);
        }
        """
        lang, _ = detector.detect_from_code(rust_code)
        assert lang == 'rust', f"Expected 'rust', got '{lang}'"

        # TypeScript code (similar type annotation syntax with ':')
        ts_code = """
        interface User {
            name: string;
            age: number;
        }

        const greet = (user: User): string => {
            return `Hello, ${user.name}`;
        }

        export type Status = 'active' | 'inactive';
        """
        lang, _ = detector.detect_from_code(ts_code)
        assert lang == 'typescript', f"Expected 'typescript', got '{lang}'"


class TestSwiftEdgeCases:
    """Test edge cases and error handling"""

    def test_swift_snippet_short(self):
        """Test short Swift snippet"""
        detector = LanguageDetector()
        code = "guard let x = optional else { return }"
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.3

    def test_swift_import_swiftui_only(self):
        """Test SwiftUI import statement alone"""
        detector = LanguageDetector()
        code = "import SwiftUI"
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.4

    def test_swift_import_uikit_only(self):
        """Test UIKit import statement alone"""
        detector = LanguageDetector()
        code = "import UIKit"
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.4

    def test_swift_import_appkit_only(self):
        """Test AppKit import statement alone"""
        detector = LanguageDetector()
        code = "import AppKit"
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.4

    def test_swift_with_comments(self):
        """Test Swift code with comments"""
        detector = LanguageDetector()
        code = """
        /// A view that displays a greeting
        struct GreetingView: View {
            // The name to display
            var name: String

            var body: some View {
                Text("Hello, \\(name)!")
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_swift_core_data(self):
        """Test Core Data code"""
        detector = LanguageDetector()
        code = """
        import CoreData

        class DataController: ObservableObject {
            let container: NSPersistentContainer

            init() {
                container = NSPersistentContainer(name: "Model")
                container.loadPersistentStores { description, error in
                    if let error = error {
                        fatalError("Core Data failed: \\(error)")
                    }
                }
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8

    def test_swift_data(self):
        """Test SwiftData code (iOS 17+)"""
        detector = LanguageDetector()
        code = """
        import SwiftData

        @Model
        class Item {
            var name: String
            var timestamp: Date

            @Relationship(deleteRule: .cascade)
            var children: [ChildItem]

            init(name: String) {
                self.name = name
                self.timestamp = Date()
            }
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.8


class TestFoundationModelsDetection:
    """Test Foundation Models framework detection (iOS/macOS 26+)"""

    def test_foundation_models_import(self):
        """Test FoundationModels import"""
        detector = LanguageDetector()
        code = "import FoundationModels"
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.4

    def test_generable_macro(self):
        """Test @Generable macro detection"""
        detector = LanguageDetector()
        code = """
        @Generable(description: "A movie recommendation")
        struct MovieRecommendation {
            @Guide(description: "The movie title")
            var title: String

            @Guide(description: "Rating from 1-5", .range(1...5))
            var rating: Int
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_language_model_session(self):
        """Test LanguageModelSession usage"""
        detector = LanguageDetector()
        code = """
        import FoundationModels

        let session = LanguageModelSession(instructions: "You are a helpful assistant")
        let response = try await session.respond(to: "Hello!")
        print(response)
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_system_language_model(self):
        """Test SystemLanguageModel usage"""
        detector = LanguageDetector()
        code = """
        import FoundationModels

        let model = SystemLanguageModel.default
        guard model.isAvailable else {
            print("Model not available")
            return
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_streaming_response(self):
        """Test streaming response pattern"""
        detector = LanguageDetector()
        code = """
        let session = LanguageModelSession(instructions: "Summarize text")
        for try await partial in session.streamResponse(to: prompt) {
            print(partial.content)
        }
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.7

    def test_guided_generation(self):
        """Test guided generation with GeneratedContent"""
        detector = LanguageDetector()
        code = """
        let response = try await session.respond(
            to: "Recommend a movie",
            generating: MovieRecommendation.self
        )
        print(response.title)
        """
        lang, confidence = detector.detect_from_code(code)
        assert lang == 'swift'
        assert confidence >= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
