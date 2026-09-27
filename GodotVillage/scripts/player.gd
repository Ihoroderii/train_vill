extends CharacterBody3D
## Controls only. Every visible object and collider is saved in a .tscn scene.

@export var walk_speed: float = 4.0
@export var run_speed: float = 7.0
@export var jump_speed: float = 6.0
@export var mouse_sensitivity: float = 0.0025

@onready var pivot: Node3D = $CameraPivot
@onready var arm: SpringArm3D = $CameraPivot/SpringArm3D
@onready var follow_camera: Camera3D = $CameraPivot/SpringArm3D/Camera3D
@onready var overview: Camera3D = get_node("../OverviewCamera")
@onready var help: Label = get_node("../HUD/BottomBar/Margin/Controls")
@onready var mode_label: Label = get_node("../HUD/TitlePanel/Margin/Column/Mode")
var exploring: bool = false
var spawn_position: Vector3

func _ready() -> void:
	spawn_position = global_position
	arm.add_excluded_object(get_rid())
	_set_exploring(true)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_TAB or event.keycode == KEY_ENTER or event.keycode == KEY_V:
			_set_exploring(not exploring)
		elif event.keycode == KEY_ESCAPE:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		elif event.keycode == KEY_R:
			global_position = spawn_position
			velocity = Vector3.ZERO
		elif event.keycode == KEY_F11:
			var window := get_window()
			window.mode = Window.MODE_WINDOWED if window.mode == Window.MODE_FULLSCREEN else Window.MODE_FULLSCREEN
		elif event.keycode == KEY_F12:
			get_viewport().get_texture().get_image().save_png("user://meadowvale.png")
	if exploring and event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
			arm.spring_length = maxf(1.5, arm.spring_length - 0.4)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			arm.spring_length = minf(7.0, arm.spring_length + 0.4)
	if exploring and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED and event is InputEventMouseMotion:
		pivot.rotation.y -= event.relative.x * mouse_sensitivity
		pivot.rotation.x = clampf(pivot.rotation.x - event.relative.y * mouse_sensitivity, -1.15, 0.3)

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= 18.0 * delta
	var movement := Vector2.ZERO
	if exploring:
		movement.x = float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
		movement.y = float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP))
		if Input.is_physical_key_pressed(KEY_SPACE) and is_on_floor():
			velocity.y = jump_speed
	var direction := Basis(Vector3.UP, pivot.rotation.y) * Vector3(movement.x, 0.0, movement.y).normalized()
	var speed := run_speed if Input.is_physical_key_pressed(KEY_SHIFT) else walk_speed
	velocity.x = move_toward(velocity.x, direction.x * speed, 24.0 * delta)
	velocity.z = move_toward(velocity.z, direction.z * speed, 24.0 * delta)
	move_and_slide()
	if global_position.y < -6.0:
		global_position = spawn_position
		velocity = Vector3.ZERO

func _set_exploring(enabled: bool) -> void:
	exploring = enabled
	follow_camera.current = enabled
	overview.current = not enabled
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if enabled else Input.MOUSE_MODE_VISIBLE
	mode_label.text = "A LITTLE PLACE TO EXPLORE" if enabled else "MEADOWVALE  /  THE MORNING EXPRESS"
	help.text = "WASD / arrows  Walk     Shift  Run     Space  Jump     Mouse  Look     Scroll  Zoom     Tab  Village view     Esc  Release mouse     R  Reset" if enabled else "ENTER  Explore the village     •     Walk as the capsule     •     TAB  Switch views"
