skill_functions = [
        {
            "type": "function",
            "function": {
                "name": "faceRecognition",
                "description": "According to the input face id, recognize and detect the face, and return the box of the id face.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "human's face id"
                        }
                    },
                    "required": ["id"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search target object.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                        }
                    },
                    "required": ["object"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "2dDetection",
                "description": "2d detect target object. return 2d box",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                        }
                    },
                    "required": ["object"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "navigation",
                "description": "navigate to target site.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site": {
                            "type": "string",
                            "description": "target site."
                        }
                    },
                    "required": ["site"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "moveTo",
                "description": "move close to target object.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                        },
                        "box": {
                            "type": "string",
                            "description": "2d box of target object.[x0, y0, x1, y1]"
                        }
                    },
                    "required": ["object", "box"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pick",
                "description": "pick/grab up target object.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                            },
                        "box": {
                            "type": "string",
                            "description": "target object's 2d box: [x0, y0, x1, y1]"
                        }
                    },
                    "required": ["object", "box"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "put",
                "description": "put object1 on object2. input box is the box of object2.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object1": {
                            "type": "string",
                            "description": "object on hand ready to be put."
                            },
                        "object2": {
                            "type": "string",
                            "description": "target location"
                            },
                        "box": {
                            "type": "string",
                            "description": "target location's 2d box: [x0, y0, x1, y1]"
                        }
                    },
                    "required": ["object1", "object2", "box"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "open",
                "description": "open target object.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                            },
                        "box": {
                            "type": "string",
                            "description": "target object's 2d box: [x0, y0, x1, y1]"
                        }
                    },
                    "required": ["object", "box"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "close",
                "description": "close target object.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                            },
                        "box": {
                            "type": "string",
                            "description": "target object's 2d box: [x0, y0, x1, y1]"
                        }
                    },
                    "required": ["object", "box"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pushButton",
                "description": "push target button.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                            },
                        "box": {
                            "type": "string",
                            "description": "target object's 2d box: [x0, y0, x1, y1]"
                        }
                    },
                    "required": ["object", "box"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "wipe",
                "description": "wipe target object area.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                            },
                        "box": {
                            "type": "string",
                            "description": "target object's 2d box: [x0, y0, x1, y1]"
                        }
                    },
                    "required": ["object", "box"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "follow",
                "description": "move follow target people by face id.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object": {
                            "type": "string",
                            "description": "target object."
                            },
                        "box": {
                            "type": "string",
                            "description": "target object's 2d box: [x0, y0, x1, y1]"
                        }
                    },
                    "required": ["object", "box"],
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "taskFinish",
                "description": "signal of task finish",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ok": {
                            "type": "string",
                            "description": "signal of task finish"
                            }
                    },
                    "required": [],
                }
            },
        }
    ]
