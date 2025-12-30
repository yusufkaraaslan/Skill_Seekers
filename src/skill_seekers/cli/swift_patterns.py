#!/usr/bin/env python3
"""
Swift Language Detection Patterns

Comprehensive regex patterns for detecting Swift code including:
- Pure Swift syntax (structs, protocols, extensions, optionals, generics)
- iOS/UIKit patterns (UIViewController, IBOutlet, lifecycle methods)
- macOS/AppKit patterns (NSViewController, NSWindow, AppKit classes)
- SwiftUI patterns (@State, @Binding, View protocol, modifiers)
- Combine framework patterns (Publishers, Subscribers)
- Swift Concurrency (async/await, actors, Tasks)
- Foundation Models (iOS/macOS 26+: @Generable, LanguageModelSession, SystemLanguageModel)

Weight Scale:
- 5: Unique to Swift (no other language uses this)
- 4: Strong Swift indicator (rarely seen elsewhere)
- 3: Common Swift pattern (moderate indicator)
- 2: Moderate indicator (seen in some other languages)
- 1: Weak indicator (commonly seen elsewhere)

Author: iLearn Project (Swift Support Extension)
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

SWIFT_PATTERNS: Dict[str, List[Tuple[str, int]]] = {
    'swift': [
        # ===== PURE SWIFT SYNTAX (Weight 4-5) =====

        # Function declarations with return type arrow (Swift-specific syntax)
        (r'\bfunc\s+\w+\s*\([^)]*\)\s*->', 5),       # func foo() -> ReturnType
        (r'\bfunc\s+\w+\s*\([^)]*\)\s*\{', 4),       # func foo() {

        # Struct/class/enum declarations
        (r'\bstruct\s+\w+\s*:', 5),                   # struct Foo: Protocol
        (r'\bstruct\s+\w+\s*\{', 4),                  # struct Foo {
        (r'\bclass\s+\w+\s*:\s*\w+', 4),              # class Foo: SuperClass
        (r'\benum\s+\w+\s*:\s*\w+', 4),               # enum Foo: String
        (r'\benum\s+\w+\s*\{', 3),                    # enum Foo {

        # Protocol declarations (weight 5 - Swift-specific in this context)
        (r'\bprotocol\s+\w+\s*\{', 5),                # protocol Foo {
        (r'\bprotocol\s+\w+\s*:\s*\w+', 5),           # protocol Foo: AnotherProtocol

        # Extension (weight 5 - very Swift-specific syntax)
        (r'\bextension\s+\w+\s*:', 5),                # extension Foo: Protocol
        (r'\bextension\s+\w+\s*\{', 5),               # extension Foo {
        (r'\bextension\s+\w+\s*where\s+', 5),         # extension Foo where T: Equatable

        # Property wrappers (weight 5 - unique to Swift)
        (r'@\w+\s+var\s+\w+', 4),                     # @Something var foo
        (r'@propertyWrapper', 5),                     # @propertyWrapper attribute

        # Optionals and unwrapping (weight 5 - unique to Swift)
        (r'\bguard\s+let\s+\w+\s*=', 5),              # guard let foo =
        (r'\bguard\s+var\s+\w+\s*=', 5),              # guard var foo =
        (r'\bif\s+let\s+\w+\s*=', 5),                 # if let foo =
        (r'\bif\s+var\s+\w+\s*=', 5),                 # if var foo =
        (r'\bguard\s+.*\s+else\s*\{', 4),             # guard ... else {
        (r'\w+\?\.', 4),                              # foo?.bar (optional chaining)
        (r'\w+!\.\w+', 4),                            # foo!.bar (forced unwrap)
        (r'\?\?', 4),                                 # nil coalescing ??

        # Closures (weight 4-5 - Swift closure syntax)
        (r'\{\s*\([^)]*\)\s*in\b', 5),                # { (params) in
        (r'\{\s*\$0', 4),                             # { $0 (shorthand argument)
        (r'\$[0-9]+', 3),                             # $0, $1, etc.

        # Type annotations (weight 3-4)
        (r':\s*\[\w+\]', 4),                          # : [Type] (array type)
        (r':\s*\[\w+\s*:\s*\w+\]', 4),                # : [Key: Value] (dictionary type)
        (r':\s*\w+\?', 4),                            # : Type? (optional type)
        (r'->\s*\w+\?', 4),                           # -> Type? (optional return)

        # Keywords (weight 2-4)
        (r'\blet\s+\w+\s*:', 3),                      # let foo: Type
        (r'\bvar\s+\w+\s*:', 3),                      # var foo: Type
        (r'\blet\s+\w+\s*=', 2),                      # let foo = (also JS const)
        (r'\bself\.\w+', 3),                          # self.property (also Python)
        (r'\bSelf\b', 4),                             # Self (Swift-specific)

        # Imports (weight 2-5 based on specificity)
        (r'\bimport\s+Foundation', 4),                # import Foundation
        (r'\bimport\s+\w+', 2),                       # import Something

        # Access modifiers (weight 3-5)
        (r'\bprivate\s*\(set\)', 5),                  # private(set) - Swift-specific
        (r'\bfileprivate\s+', 5),                     # fileprivate - Swift-only keyword
        (r'\binternal\s+', 2),                        # internal (also C#)
        (r'\bopen\s+class', 4),                       # open class (Swift-specific)

        # Error handling (weight 4-5)
        (r'\bthrows\s*->', 5),                        # throws -> ReturnType
        (r'\bthrows\s*\{', 4),                        # func foo() throws {
        (r'\brethrows\b', 5),                         # rethrows keyword (Swift-only)
        (r'\btry\?\s+', 5),                           # try? (optional try - Swift)
        (r'\btry!\s+', 5),                            # try! (forced try - Swift)
        (r'\bdo\s*\{', 3),                            # do { (try block)
        (r'\bcatch\s+\w+', 3),                        # catch error

        # Generics (weight 3-4)
        (r'<\w+:\s*\w+>', 4),                         # <T: Protocol>
        (r'\bwhere\s+\w+\s*:', 4),                    # where T: Protocol
        # NOTE: 'some' and 'any' require capitalized type names to avoid matching
        # English prose ("some example", "any variable"). Swift types are capitalized
        # by convention (View, Protocol, etc.). The (?-i:[A-Z]) syntax enforces
        # case-sensitive matching for the first letter despite global IGNORECASE flag.
        (r'\bsome\s+(?-i:[A-Z])\w+', 5),              # some Protocol (opaque type - Swift 5.1+)
        (r'\bany\s+(?-i:[A-Z])\w+', 4),               # any Protocol (existential type - Swift 5.6+)

        # Actors and concurrency (weight 5 - Swift 5.5+)
        (r'\bactor\s+\w+', 5),                        # actor MyActor
        (r'\basync\s+throws', 5),                     # async throws (Swift-specific combo)
        (r'\basync\s+func', 5),                       # async func
        (r'\bawait\s+\w+', 3),                        # await (also JS/Python/C#)
        (r'\bTask\s*\{', 4),                          # Task { (Swift concurrency)
        (r'\bTask\.\w+', 4),                          # Task.detached, Task.sleep
        (r'@MainActor', 5),                           # @MainActor attribute
        (r'@Sendable', 5),                            # @Sendable attribute
        (r'\bnonisolated\b', 5),                      # nonisolated keyword

        # Result builders (weight 5)
        (r'@resultBuilder', 5),                       # @resultBuilder attribute

        # Type aliases and associated types (weight 5)
        (r'\btypealias\s+\w+\s*=', 5),                # typealias Foo = Bar
        (r'\bassociatedtype\s+\w+', 5),               # associatedtype Element

        # Print function
        (r'\bprint\s*\(', 2),                         # print() (also Python)

        # String interpolation (weight 4)
        (r'\\\(\w+', 4),                              # \(variable) interpolation

        # Memory management (weight 4-5)
        (r'\bweak\s+var', 5),                         # weak var
        (r'\bunowned\s+', 5),                         # unowned (Swift-specific)
        (r'\[weak\s+self\]', 5),                      # [weak self] capture list
        (r'\[unowned\s+self\]', 5),                   # [unowned self] capture list
        (r'\blazy\s+var', 4),                         # lazy var

        # ===== iOS/UIKit PATTERNS (Weight 4-5) =====

        (r'\bimport\s+UIKit', 5),                     # import UIKit
        (r'\bUIViewController\b', 5),                 # UIViewController class
        (r'\bUIView\b', 4),                           # UIView class
        (r'\bUITableView\b', 5),                      # UITableView
        (r'\bUICollectionView\b', 5),                 # UICollectionView
        (r'\bUINavigationController\b', 5),           # UINavigationController
        (r'\bUITabBarController\b', 5),               # UITabBarController
        (r'\bUIButton\b', 4),                         # UIButton
        (r'\bUILabel\b', 4),                          # UILabel
        (r'\bUIImageView\b', 4),                      # UIImageView
        (r'\bUITextField\b', 4),                      # UITextField
        (r'\bUITextView\b', 4),                       # UITextView
        (r'\bUIStackView\b', 4),                      # UIStackView
        (r'\bUIScrollView\b', 4),                     # UIScrollView
        (r'\bUIAlertController\b', 5),                # UIAlertController
        (r'\bUIApplication\b', 5),                    # UIApplication
        (r'\bUIWindow\b', 4),                         # UIWindow
        (r'\bUIScreen\b', 4),                         # UIScreen
        (r'\bUIDevice\b', 5),                         # UIDevice

        # UIKit Lifecycle methods (weight 5)
        (r'\bviewDidLoad\s*\(\s*\)', 5),              # viewDidLoad()
        (r'\bviewWillAppear\s*\(', 5),                # viewWillAppear(_:)
        (r'\bviewDidAppear\s*\(', 5),                 # viewDidAppear(_:)
        (r'\bviewWillDisappear\s*\(', 5),             # viewWillDisappear(_:)
        (r'\bviewDidDisappear\s*\(', 5),              # viewDidDisappear(_:)
        (r'\bviewWillLayoutSubviews\s*\(\)', 5),      # viewWillLayoutSubviews()
        (r'\bviewDidLayoutSubviews\s*\(\)', 5),       # viewDidLayoutSubviews()

        # Interface Builder outlets/actions (weight 5)
        (r'@IBOutlet', 5),                            # @IBOutlet
        (r'@IBAction', 5),                            # @IBAction
        (r'@IBDesignable', 5),                        # @IBDesignable
        (r'@IBInspectable', 5),                       # @IBInspectable

        # UIKit delegates and datasources (weight 5)
        (r'\bUITableViewDelegate\b', 5),
        (r'\bUITableViewDataSource\b', 5),
        (r'\bUICollectionViewDelegate\b', 5),
        (r'\bUICollectionViewDataSource\b', 5),
        (r'\bUITextFieldDelegate\b', 5),
        (r'\bUIScrollViewDelegate\b', 5),

        # Auto Layout (weight 4-5)
        (r'\bNSLayoutConstraint\b', 5),               # NSLayoutConstraint
        (r'\.constraint\(', 4),                       # constraint methods
        (r'\btranslatesAutoresizingMaskIntoConstraints', 5),
        (r'NSLayoutConstraint\.activate', 5),

        # GCD / DispatchQueue (weight 5)
        (r'\bDispatchQueue\b', 5),                    # DispatchQueue
        (r'\bDispatchQueue\.main', 5),                # DispatchQueue.main
        (r'\bDispatchQueue\.global', 5),              # DispatchQueue.global
        (r'\.async\s*\{', 4),                         # .async {
        (r'\.sync\s*\{', 4),                          # .sync {

        # ===== macOS/AppKit PATTERNS (Weight 4-5) =====

        (r'\bimport\s+AppKit', 5),                    # import AppKit
        (r'\bimport\s+Cocoa', 5),                     # import Cocoa
        (r'\bNSViewController\b', 5),                 # NSViewController
        (r'\bNSView\b', 4),                           # NSView
        (r'\bNSWindow\b', 5),                         # NSWindow
        (r'\bNSWindowController\b', 5),               # NSWindowController
        (r'\bNSApplication\b', 5),                    # NSApplication
        (r'\bNSTableView\b', 5),                      # NSTableView
        (r'\bNSOutlineView\b', 5),                    # NSOutlineView
        (r'\bNSCollectionView\b', 5),                 # NSCollectionView
        (r'\bNSButton\b', 4),                         # NSButton
        (r'\bNSTextField\b', 4),                      # NSTextField
        (r'\bNSTextView\b', 4),                       # NSTextView
        (r'\bNSImageView\b', 4),                      # NSImageView
        (r'\bNSStackView\b', 4),                      # NSStackView
        (r'\bNSScrollView\b', 4),                     # NSScrollView
        (r'\bNSSplitView\b', 5),                      # NSSplitView
        (r'\bNSTabView\b', 5),                        # NSTabView
        (r'\bNSMenu\b', 5),                           # NSMenu
        (r'\bNSMenuItem\b', 5),                       # NSMenuItem
        (r'\bNSToolbar\b', 5),                        # NSToolbar
        (r'\bNSAlert\b', 5),                          # NSAlert
        (r'\bNSPanel\b', 5),                          # NSPanel
        (r'\bNSOpenPanel\b', 5),                      # NSOpenPanel
        (r'\bNSSavePanel\b', 5),                      # NSSavePanel
        (r'\bNSWorkspace\b', 5),                      # NSWorkspace
        (r'\bNSRunningApplication\b', 5),             # NSRunningApplication
        (r'\bNSScreen\b', 4),                         # NSScreen
        (r'\bNSColor\b', 4),                          # NSColor
        (r'\bNSFont\b', 4),                           # NSFont
        (r'\bNSImage\b', 4),                          # NSImage
        (r'\bNSBezierPath\b', 5),                     # NSBezierPath
        (r'\bNSSound\b', 5),                          # NSSound
        (r'\bNSEvent\b', 5),                          # NSEvent
        (r'\bNSResponder\b', 5),                      # NSResponder
        (r'\bNSPasteboard\b', 5),                     # NSPasteboard
        (r'\bNSStatusBar\b', 5),                      # NSStatusBar
        (r'\bNSStatusItem\b', 5),                     # NSStatusItem

        # macOS Lifecycle methods (weight 5)
        # Note: viewDidLoad() is defined in the UIKit section above since it's shared
        # between iOS (UIViewController) and macOS (NSViewController)
        (r'\bviewWillAppear\s*\(\)', 5),              # NSViewController viewWillAppear
        (r'\bviewDidAppear\s*\(\)', 5),               # NSViewController viewDidAppear
        (r'\bawakeFromNib\s*\(\)', 5),                # awakeFromNib()
        (r'\bapplicationDidFinishLaunching', 5),      # NSApplicationDelegate
        (r'\bapplicationWillTerminate', 5),           # NSApplicationDelegate
        (r'\bwindowDidLoad\s*\(\)', 5),               # NSWindowController

        # macOS delegates (weight 5)
        (r'\bNSTableViewDelegate\b', 5),
        (r'\bNSTableViewDataSource\b', 5),
        (r'\bNSOutlineViewDelegate\b', 5),
        (r'\bNSOutlineViewDataSource\b', 5),
        (r'\bNSWindowDelegate\b', 5),
        (r'\bNSApplicationDelegate\b', 5),
        (r'\bNSTextFieldDelegate\b', 5),
        (r'\bNSTextViewDelegate\b', 5),

        # ===== SwiftUI PATTERNS (Weight 5) =====

        (r'\bimport\s+SwiftUI', 5),                   # import SwiftUI
        (r'\bstruct\s+\w+\s*:\s*View', 5),            # struct Foo: View
        (r'\bvar\s+body\s*:\s*some\s+View', 5),       # var body: some View
        (r':\s*some\s+View', 5),                      # : some View

        # SwiftUI property wrappers (weight 5 - unique to SwiftUI)
        (r'@State\s+', 5),                            # @State var
        (r'@Binding\s+', 5),                          # @Binding var
        (r'@Published\s+', 5),                        # @Published var
        (r'@ObservedObject\s+', 5),                   # @ObservedObject var
        (r'@StateObject\s+', 5),                      # @StateObject var
        (r'@EnvironmentObject\s+', 5),                # @EnvironmentObject var
        (r'@Environment\s*\(', 5),                    # @Environment(\.keyPath)
        (r'@FetchRequest\s*\(', 5),                   # @FetchRequest (Core Data)
        (r'@AppStorage\s*\(', 5),                     # @AppStorage
        (r'@SceneStorage\s*\(', 5),                   # @SceneStorage
        (r'@FocusState\s+', 5),                       # @FocusState
        (r'@FocusedBinding\s*\(', 5),                 # @FocusedBinding
        (r'@Observable\b', 5),                        # @Observable (Swift 5.9+)
        (r'@Bindable\s+', 5),                         # @Bindable (Swift 5.9+)
        (r'@Query\s*\(', 5),                          # @Query (SwiftData)
        (r'@Model\b', 5),                             # @Model (SwiftData)
        (r'@ViewBuilder', 5),                         # @ViewBuilder

        # SwiftUI Views (weight 4-5)
        (r'\bText\s*\(', 4),                          # Text("Hello")
        (r'\bImage\s*\(', 3),                         # Image(systemName:)
        (r'\bButton\s*\(', 3),                        # Button("Label") { }
        (r'\bVStack\s*[\(\{]', 5),                    # VStack { } or VStack(alignment:)
        (r'\bHStack\s*[\(\{]', 5),                    # HStack { }
        (r'\bZStack\s*[\(\{]', 5),                    # ZStack { }
        (r'\bList\s*[\(\{]', 4),                      # List { }
        (r'\bForEach\s*\(', 4),                       # ForEach(items) { }
        (r'\bNavigationView\s*\{', 5),                # NavigationView { }
        (r'\bNavigationStack\s*[\(\{]', 5),           # NavigationStack { } (iOS 16+)
        (r'\bNavigationSplitView\s*[\(\{]', 5),       # NavigationSplitView (macOS/iPad)
        (r'\bNavigationLink\s*\(', 5),                # NavigationLink
        (r'\bTabView\s*[\(\{]', 5),                   # TabView { }
        (r'\bScrollView\s*[\(\{]', 5),                # ScrollView { }
        (r'\bLazyVStack\s*[\(\{]', 5),                # LazyVStack { }
        (r'\bLazyHStack\s*[\(\{]', 5),                # LazyHStack { }
        (r'\bLazyVGrid\s*\(', 5),                     # LazyVGrid
        (r'\bLazyHGrid\s*\(', 5),                     # LazyHGrid
        (r'\bGrid\s*[\(\{]', 4),                      # Grid { } (iOS 16+)
        (r'\bGridRow\s*[\(\{]', 5),                   # GridRow { }
        (r'\bGeometryReader\s*\{', 5),                # GeometryReader { }
        (r'\bSpacer\s*\(\)', 5),                      # Spacer()
        (r'\bDivider\s*\(\)', 5),                     # Divider()
        (r'\bForm\s*\{', 4),                          # Form { }
        (r'\bSection\s*[\(\{]', 4),                   # Section { }
        (r'\bGroup\s*\{', 4),                         # Group { }
        (r'\bGroupBox\s*[\(\{]', 5),                  # GroupBox { }
        (r'\bDisclosureGroup\s*\(', 5),               # DisclosureGroup
        (r'\bOutlineGroup\s*\(', 5),                  # OutlineGroup
        (r'\bToggle\s*\(', 4),                        # Toggle
        (r'\bPicker\s*\(', 4),                        # Picker
        (r'\bSlider\s*\(', 4),                        # Slider
        (r'\bStepper\s*\(', 4),                       # Stepper
        (r'\bDatePicker\s*\(', 5),                    # DatePicker
        (r'\bColorPicker\s*\(', 5),                   # ColorPicker
        (r'\bProgressView\s*[\(\{]', 5),              # ProgressView
        (r'\bLabel\s*\(', 4),                         # Label
        (r'\bLink\s*\(', 4),                          # Link
        (r'\bMenu\s*[\(\{]', 4),                      # Menu
        (r'\bContextMenu\s*\{', 5),                   # ContextMenu
        (r'\bToolbar\s*\{', 5),                       # Toolbar
        (r'\bToolbarItem\s*\(', 5),                   # ToolbarItem
        (r'\bCanvas\s*\{', 5),                        # Canvas
        (r'\bTimelineView\s*\(', 5),                  # TimelineView
        (r'\bShareLink\s*\(', 5),                     # ShareLink (iOS 16+)
        (r'\bPhotosPicker\s*\(', 5),                  # PhotosPicker
        (r'\bTextField\s*\(', 4),                     # TextField
        (r'\bSecureField\s*\(', 5),                   # SecureField
        (r'\bTextEditor\s*\(', 5),                    # TextEditor

        # SwiftUI Modifiers (weight 4-5)
        (r'\.padding\s*\(', 4),                       # .padding()
        (r'\.frame\s*\(', 4),                         # .frame(width:height:)
        (r'\.foregroundColor\s*\(', 5),               # .foregroundColor(.red)
        (r'\.foregroundStyle\s*\(', 5),               # .foregroundStyle (iOS 15+)
        (r'\.background\s*\(', 3),                    # .background()
        (r'\.cornerRadius\s*\(', 4),                  # .cornerRadius()
        (r'\.clipShape\s*\(', 5),                     # .clipShape()
        (r'\.shadow\s*\(', 3),                        # .shadow()
        (r'\.font\s*\(', 3),                          # .font(.title)
        (r'\.fontWeight\s*\(', 4),                    # .fontWeight()
        (r'\.bold\s*\(\)', 4),                        # .bold()
        (r'\.italic\s*\(\)', 4),                      # .italic()
        (r'\.onAppear\s*\{', 5),                      # .onAppear { }
        (r'\.onDisappear\s*\{', 5),                   # .onDisappear { }
        (r'\.onTapGesture\s*\{', 5),                  # .onTapGesture { }
        (r'\.gesture\s*\(', 4),                       # .gesture()
        (r'\.sheet\s*\(', 5),                         # .sheet(isPresented:)
        (r'\.fullScreenCover\s*\(', 5),               # .fullScreenCover()
        (r'\.popover\s*\(', 5),                       # .popover()
        (r'\.alert\s*\(', 4),                         # .alert()
        (r'\.confirmationDialog\s*\(', 5),            # .confirmationDialog()
        (r'\.navigationTitle\s*\(', 5),               # .navigationTitle()
        (r'\.navigationBarTitleDisplayMode', 5),      # .navigationBarTitleDisplayMode
        (r'\.toolbar\s*\{', 5),                       # .toolbar { }
        (r'\.toolbarBackground\s*\(', 5),             # .toolbarBackground()
        (r'\.environmentObject\s*\(', 5),             # .environmentObject()
        (r'\.environment\s*\(', 4),                   # .environment()
        (r'\.task\s*\{', 5),                          # .task { } (async)
        (r'\.refreshable\s*\{', 5),                   # .refreshable { }
        (r'\.searchable\s*\(', 5),                    # .searchable()
        (r'\.onChange\s*\(', 5),                      # .onChange(of:)
        (r'\.onSubmit\s*\{', 5),                      # .onSubmit { }
        (r'\.focused\s*\(', 5),                       # .focused()
        (r'\.disabled\s*\(', 4),                      # .disabled()
        (r'\.opacity\s*\(', 3),                       # .opacity()
        (r'\.offset\s*\(', 4),                        # .offset()
        (r'\.rotationEffect\s*\(', 5),                # .rotationEffect()
        (r'\.scaleEffect\s*\(', 5),                   # .scaleEffect()
        (r'\.animation\s*\(', 4),                     # .animation()
        (r'\.transition\s*\(', 5),                    # .transition()
        (r'\.withAnimation\s*\{', 5),                 # withAnimation { }
        (r'\.matchedGeometryEffect\s*\(', 5),         # .matchedGeometryEffect()
        (r'\.contentShape\s*\(', 5),                  # .contentShape()
        (r'\.allowsHitTesting\s*\(', 5),              # .allowsHitTesting()
        (r'\.overlay\s*\(', 4),                       # .overlay()
        (r'\.mask\s*\(', 4),                          # .mask()
        (r'\.zIndex\s*\(', 4),                        # .zIndex()
        (r'\.layoutPriority\s*\(', 5),                # .layoutPriority()
        (r'\.preference\s*\(', 5),                    # .preference()
        (r'\.onPreferenceChange\s*\(', 5),            # .onPreferenceChange()
        (r'\.coordinateSpace\s*\(', 5),               # .coordinateSpace()
        (r'\.ignoresSafeArea\s*\(', 5),               # .ignoresSafeArea()
        (r'\.safeAreaInset\s*\(', 5),                 # .safeAreaInset()
        (r'\.listStyle\s*\(', 5),                     # .listStyle()
        (r'\.buttonStyle\s*\(', 5),                   # .buttonStyle()
        (r'\.textFieldStyle\s*\(', 5),                # .textFieldStyle()
        (r'\.pickerStyle\s*\(', 5),                   # .pickerStyle()
        (r'\.labelStyle\s*\(', 5),                    # .labelStyle()
        (r'\.toggleStyle\s*\(', 5),                   # .toggleStyle()
        (r'\.presentationDetents\s*\(', 5),           # .presentationDetents() (iOS 16+)
        (r'\.interactiveDismissDisabled\s*\(', 5),    # .interactiveDismissDisabled()

        # SwiftUI Scene types (macOS/multi-window)
        (r'\bWindowGroup\s*\{', 5),                   # WindowGroup { }
        (r'\bWindow\s*\(', 5),                        # Window (macOS)
        (r'\bSettings\s*\{', 5),                      # Settings { } (macOS)
        (r'\bMenuBarExtra\s*\(', 5),                  # MenuBarExtra (macOS)
        (r'\bDocumentGroup\s*\(', 5),                 # DocumentGroup
        (r':\s*App\s*\{', 5),                         # : App {
        (r'@main\b', 5),                              # @main
        (r'var\s+body:\s*some\s+Scene', 5),           # var body: some Scene

        # ===== Combine Framework (Weight 5) =====

        (r'\bimport\s+Combine', 5),                   # import Combine
        (r'\bAnyPublisher\b', 5),                     # AnyPublisher
        (r'\bPassthroughSubject\b', 5),               # PassthroughSubject
        (r'\bCurrentValueSubject\b', 5),              # CurrentValueSubject
        (r'\bPublisher\b', 4),                        # Publisher protocol
        (r'\bSubscriber\b', 4),                       # Subscriber protocol
        (r'\.sink\s*\{', 5),                          # .sink { }
        (r'\.receive\s*\(on:\s*', 5),                 # .receive(on: RunLoop.main)
        (r'\bAnyCancellable\b', 5),                   # AnyCancellable
        (r'\.store\s*\(in:\s*&', 5),                  # .store(in: &cancellables)
        (r'\.eraseToAnyPublisher\s*\(\)', 5),         # .eraseToAnyPublisher()
        (r'\.map\s*\{\s*\$0', 5),                     # .map { $0 (Combine map)
        (r'\.flatMap\s*\{', 4),                       # .flatMap {
        (r'\.compactMap\s*\{', 4),                    # .compactMap {
        (r'\.filter\s*\{', 3),                        # .filter {
        (r'\.debounce\s*\(', 5),                      # .debounce()
        (r'\.throttle\s*\(', 5),                      # .throttle()
        (r'\.removeDuplicates\s*\(', 5),              # .removeDuplicates()
        (r'\.combineLatest\s*\(', 5),                 # .combineLatest()
        (r'\.merge\s*\(', 4),                         # .merge()
        (r'\.zip\s*\(', 3),                           # .zip()
        (r'@Published\s+var', 5),                     # @Published var

        # ===== Codable/JSON (Weight 5) =====

        (r'\bCodable\b', 5),                          # Codable protocol
        (r'\bEncodable\b', 4),                        # Encodable protocol
        (r'\bDecodable\b', 4),                        # Decodable protocol
        (r'\bJSONDecoder\s*\(\)', 5),                 # JSONDecoder()
        (r'\bJSONEncoder\s*\(\)', 5),                 # JSONEncoder()
        (r'\bCodingKeys\b', 5),                       # CodingKeys enum
        (r'\bPropertyListDecoder\b', 5),              # PropertyListDecoder
        (r'\bPropertyListEncoder\b', 5),              # PropertyListEncoder

        # ===== Core Data (Weight 5) =====

        (r'\bimport\s+CoreData', 5),                  # import CoreData
        (r'\bNSManagedObject\b', 5),                  # NSManagedObject
        (r'\bNSManagedObjectContext\b', 5),           # NSManagedObjectContext
        (r'\bNSPersistentContainer\b', 5),            # NSPersistentContainer
        (r'\bNSFetchRequest\b', 5),                   # NSFetchRequest
        (r'\b@FetchRequest\b', 5),                    # @FetchRequest property wrapper
        (r'\bNSPredicate\b', 5),                      # NSPredicate
        (r'\bNSSortDescriptor\b', 5),                 # NSSortDescriptor

        # ===== SwiftData (Weight 5 - iOS 17+) =====

        (r'\bimport\s+SwiftData', 5),                 # import SwiftData
        (r'@Model\s+', 5),                            # @Model class
        (r'@Attribute\s*\(', 5),                      # @Attribute
        (r'@Relationship\s*\(', 5),                   # @Relationship
        (r'\bModelContext\b', 5),                     # ModelContext
        (r'\bModelContainer\b', 5),                   # ModelContainer

        # ===== Common Apple Frameworks (Weight 4-5) =====

        (r'\bimport\s+MapKit', 5),                    # import MapKit
        (r'\bimport\s+CoreLocation', 5),              # import CoreLocation
        (r'\bimport\s+AVFoundation', 5),              # import AVFoundation
        (r'\bimport\s+Photos', 5),                    # import Photos
        (r'\bimport\s+PhotosUI', 5),                  # import PhotosUI
        (r'\bimport\s+HealthKit', 5),                 # import HealthKit
        (r'\bimport\s+StoreKit', 5),                  # import StoreKit
        (r'\bimport\s+CloudKit', 5),                  # import CloudKit
        (r'\bimport\s+UserNotifications', 5),         # import UserNotifications
        (r'\bimport\s+EventKit', 5),                  # import EventKit
        (r'\bimport\s+Contacts', 5),                  # import Contacts
        (r'\bimport\s+MessageUI', 5),                 # import MessageUI
        (r'\bimport\s+SafariServices', 5),            # import SafariServices
        (r'\bimport\s+WebKit', 5),                    # import WebKit
        (r'\bimport\s+PDFKit', 5),                    # import PDFKit
        (r'\bimport\s+QuickLook', 5),                 # import QuickLook
        (r'\bimport\s+AuthenticationServices', 5),    # import AuthenticationServices
        (r'\bimport\s+LocalAuthentication', 5),       # import LocalAuthentication
        (r'\bimport\s+GameKit', 5),                   # import GameKit
        (r'\bimport\s+SpriteKit', 5),                 # import SpriteKit
        (r'\bimport\s+SceneKit', 5),                  # import SceneKit
        (r'\bimport\s+RealityKit', 5),                # import RealityKit
        (r'\bimport\s+ARKit', 5),                     # import ARKit
        (r'\bimport\s+Metal', 5),                     # import Metal
        (r'\bimport\s+CoreML', 5),                    # import CoreML
        (r'\bimport\s+Vision', 5),                    # import Vision
        (r'\bimport\s+NaturalLanguage', 5),           # import NaturalLanguage
        (r'\bimport\s+Speech', 5),                    # import Speech
        (r'\bimport\s+CoreBluetooth', 5),             # import CoreBluetooth
        (r'\bimport\s+NetworkExtension', 5),          # import NetworkExtension
        (r'\bimport\s+WidgetKit', 5),                 # import WidgetKit
        (r'\bimport\s+ActivityKit', 5),               # import ActivityKit
        (r'\bimport\s+AppIntents', 5),                # import AppIntents

        # ===== Foundation Models Framework (iOS/macOS/visionOS 26+) =====
        # Apple's on-device AI/ML framework for language model interactions

        # Import statement
        (r'\bimport\s+FoundationModels', 5),          # import FoundationModels

        # Core classes
        (r'\bSystemLanguageModel\b', 5),              # Main model class
        (r'\bLanguageModelSession\b', 5),             # Session for interactions
        (r'\bLanguageModelFeedback\b', 5),            # Feedback reporting

        # Key structs
        (r'\bInstructionsBuilder\b', 5),              # Result builder for instructions
        (r'\bPromptBuilder\b', 5),                    # Result builder for prompts
        (r'\bGenerationOptions\b', 5),                # Controls generation behavior
        (r'\bGeneratedContent\b', 5),                 # Structured output type
        (r'\bGenerationID\b', 5),                     # Unique generation identifier
        (r'\bGenerationSchema\b', 5),                 # Schema for guided generation
        (r'\bDynamicGenerationSchema\b', 5),          # Runtime schema definition
        (r'\bGenerationGuide\b', 5),                  # Value constraint guides

        # Macros (unique to FoundationModels)
        (r'@Generable\b', 5),                         # Guided generation macro
        (r'@Generable\s*\(\s*description:', 5),       # @Generable with description
        (r'@Guide\b', 5),                             # Property constraint macro
        (r'@Guide\s*\(\s*description:', 5),           # @Guide with description

        # Key protocols
        (r'\bGenerable\b', 4),                        # Core protocol (also common word)
        (r'\bInstructionsRepresentable\b', 5),        # Instructions protocol
        (r'\bPromptRepresentable\b', 5),              # Prompt protocol
        (r'\bConvertibleFromGeneratedContent\b', 5),  # Content conversion
        (r'\bConvertibleToGeneratedContent\b', 5),    # Content conversion

        # Nested types (SystemLanguageModel.*)
        (r'\bSystemLanguageModel\.default\b', 5),     # Default model access
        (r'\bSystemLanguageModel\.UseCase\b', 5),     # Use case type
        (r'\bSystemLanguageModel\.Guardrails\b', 5),  # Safety guardrails
        (r'\bSystemLanguageModel\.Adapter\b', 5),     # Custom adapters
        (r'\bSystemLanguageModel\.Availability\b', 5), # Availability enum

        # Key methods
        (r'\.respond\s*\(to:', 4),                    # Primary response method
        (r'\.respond\s*\([^)]*generating:', 5),       # Guided generation response
        (r'\.streamResponse\s*\(', 4),                # Streaming response
        (r'\.prewarm\s*\(', 5),                       # Session prewarming
        (r'\.logFeedbackAttachment\s*\(', 5),         # Feedback logging

        # Transcript types
        (r'\bTranscript\.Entry\b', 5),                # Transcript entry
        (r'\bTranscript\.Segment\b', 5),              # Transcript segment
        (r'\bTranscript\.ToolCall\b', 5),             # Tool call record
        (r'\bTranscript\.ToolOutput\b', 5),           # Tool output record
        (r'\bTranscript\.Response\b', 5),             # Response record

        # Error types and availability
        (r'\bGenerationError\b', 4),                  # Generation error type
        (r'\bToolCallError\b', 5),                    # Tool execution error
        (r'\.exceededContextWindowSize\b', 5),        # Context window error
        (r'\.guardrailViolation\b', 5),               # Safety guardrail error
        (r'\.appleIntelligenceNotEnabled\b', 5),      # Availability reason
        (r'\.deviceNotEligible\b', 5),                # Device eligibility
        (r'\.modelNotReady\b', 5),                    # Model readiness

        # Use cases and guardrails
        (r'\.contentTagging\b', 5),                   # Content tagging use case
        (r'\.permissiveContentTransformations\b', 5), # Guardrail setting

        # Common usage patterns
        (r'LanguageModelSession\s*\(\s*instructions:', 5),  # Session init
        (r'for\s+try\s+await.*streamResponse', 5),    # Streaming iteration
        (r'\.PartiallyGenerated\b', 5),               # Partial generation type
    ],
}


def _validate_patterns(patterns: Dict[str, List[Tuple[str, int]]]) -> None:
    """
    Validate pattern structure at module load time.

    Ensures all patterns follow the expected format:
    - Each pattern is a (regex_string, weight) tuple
    - Weight is an integer between 1 and 5
    - Regex string is a valid string

    Raises:
        ValueError: If any pattern is malformed
    """
    for lang, pattern_list in patterns.items():
        for i, item in enumerate(pattern_list):
            if not isinstance(item, tuple) or len(item) != 2:
                raise ValueError(
                    f"Pattern {i} for '{lang}' is not a (regex, weight) tuple: {item}"
                )
            pattern, weight = item
            if not isinstance(pattern, str):
                raise ValueError(
                    f"Pattern {i} for '{lang}': regex must be a string, got {type(pattern).__name__}"
                )
            if not isinstance(weight, int) or weight < 1 or weight > 5:
                raise ValueError(
                    f"Pattern {i} for '{lang}': weight must be int 1-5, got {weight!r}"
                )


# Validate patterns at module load time
try:
    _validate_patterns(SWIFT_PATTERNS)
except ValueError as e:
    logger.error(
        "Swift pattern validation failed: %s. Swift detection will be disabled. "
        "This indicates a bug in swift_patterns.py - please file an issue.",
        e
    )
    # Clear patterns to prevent broken detection with invalid data
    SWIFT_PATTERNS = {}
