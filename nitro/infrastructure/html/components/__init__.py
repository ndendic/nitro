from .utils import cva, cn, uniq

from .inputs import *
# from .monsterui.all import *
from .codeblock import CodeBlock
from .tabs import Tabs, TabsList, TabsTrigger, TabsContent
from .accordion import Accordion, AccordionItem
from .dialog import (
    Dialog,
    DialogTrigger,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogBody,
    DialogFooter,
    DialogClose,
)
from .icons import LucideIcon

# P0 Foundation Components
from .button import Button, ButtonGroup
from .card import Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
from .badge import Badge
from .alert import Alert, AlertTitle, AlertDescription
from .label import Label
from .kbd import Kbd
from .spinner import Spinner
from .skeleton import Skeleton

# P1 Form Controls
from .checkbox import Checkbox
from .radio import RadioGroup, RadioItem
from .switch import Switch
from .select import Select, SelectOption, SelectOptGroup
from .textarea import Textarea
from .field import Field, Fieldset
from .input_group import InputGroup
from .calendar import Calendar
from .datepicker import DatePicker, DateRangePicker
from .dropzone import Dropzone, DropzoneItem, DropzoneList

# P2 Interactive Overlays
from .dropdown import (
    DropdownMenu,
    DropdownTrigger,
    DropdownContent,
    DropdownItem,
    DropdownSeparator,
    DropdownLabel,
)
from .popover import (
    Popover,
    PopoverTrigger,
    PopoverContent,
    PopoverClose,
)
from .tooltip import Tooltip
from .alert_dialog import (
    AlertDialog,
    AlertDialogTrigger,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogAction,
    AlertDialogCancel,
)

# P3 Feedback Components
from .toast import (
    ToastProvider,
    Toaster,
    Toast,
    ToastTrigger,
    ToastClose,
)
from .progress import Progress

# P4 Navigation & Display
from .breadcrumb import (
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbSeparator,
    BreadcrumbEllipsis,
)
from .pagination import Pagination, PaginationContent
from .avatar import Avatar, AvatarGroup, DiceBearAvatar
from .table import (
    Table,
    TableHeader,
    TableBody,
    TableFooter,
    TableRow,
    TableHead,
    TableCell,
    TableCaption,
)

# P5 Advanced Components
from .combobox import (
    Combobox,
    ComboboxItem,
    ComboboxGroup,
    ComboboxSeparator,
)
from .command import (
    Command,
    CommandDialog,
    CommandGroup,
    CommandItem,
    CommandSeparator,
    CommandEmpty,
)
from .theme_switcher import (
    ThemeSwitcher,
    ThemeSwitcherDropdown,
    ThemeSelect,
)

# P6 Layout Components
from .sidebar import (
    Sidebar,
    SidebarHeader,
    SidebarContent,
    SidebarFooter,
    SidebarToggle,
    # New navigation components
    SidebarMenu,
    SidebarSectionTitle,
    SidebarLink,
    SidebarItem,
    SidebarSubmenu,
    SidebarDivider,
    # Legacy components (kept for backward compatibility)
    SidebarNav,
    SidebarGroup,
    SidebarGroupLabel,
    SidebarCollapsible,
    SidebarSeparator,
    create_nav_item,
)

from .base import *
from .base_layouts import *
from .charts import ApexChart, ChartT